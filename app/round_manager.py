# Description:  This file contains the routes and socket events used for handling user requests.
# Path:         app/routes.py
# Author:       Capucinoxx
# Date:         2024

import time
from datetime import datetime, timezone, timedelta
from typing import List, Union, Tuple

import eventlet
from flask import Flask, current_app
from flask_socketio import SocketIO

from app.models import Challenge, Submission, Team, User, SubmissionType, persist_sumbissions
from app.utils import CDict, logger
from app.cmd.app import app


class RoundManager:
  """
    Manages the rounds of art-forgery, handling the start, end, and the progression
    of rounds, as well as managing submissions within each round.
  """
  def __init__(self):
    self.__rounds = []
    self.__round_duration = 0
    self.__current_round = None
    self.__current_round_start = None
    self.__is_running = False
    self.__app_context = None
    self.__current_challenge = None
    self.__submissions = CDict()
    self.__lock = eventlet.semaphore.Semaphore()


  def init_app(self, app: Flask, socketio: SocketIO) -> None:
    """
      Initializes the RoundManager with the Flask app and SocketIO instance, setting up context 
      and configurations.

      Args:
        app (Flask): The Flask app instance.
        socketio (SocketIO): The SocketIO instance.
    """
    self.__app_context = app.app_context()
    self.__app_context.push()
    self.__socket = socketio

    self.__round_duration = app.config.get('ROUND_DURATION', 35 * 60)
    self.__break_duration = app.config.get('BREAK_DURATION', 5 * 60)
    self.__rounds: List[Challenge] = list(Challenge.objects.order_by('_id'))


  def start(self) -> None:
    """
      Starts the round management process.
    """
    with self.__lock:
      if self.__is_running:
        return

      self.__is_running = True
    eventlet.spawn(self.__run)


  def current_round_is_active(self) -> bool:
    """
      Checks if the current round is active based on the time elapsed.

      Returns:
        bool: True if the current round is active, otherwise False.
    """
    with self.__lock:
      return self.__current_round != None and time.time() < self.__current_round_start + self.__round_duration


  def retrieve_role(self, id: int) -> SubmissionType:
    """
      Determines the role (e.g., CSS or HTML) based on the participant's ID and current round.

      Args:
        id (int): The participant's ID.

      Returns:
        SubmissionType: The role of the participant.
    """
    if self.__current_round == None or self.__current_round % 2 == 1:
      return SubmissionType.CSS if id == 1 else SubmissionType.HTML
    else:
      return SubmissionType.HTML if id == 1 else SubmissionType.CSS


  def current(self) -> Union[Tuple[int, Challenge], None]:
    """
      Retrieves the current round number and the associated Challenge.

      Returns:
        Union[Tuple[int, Challenge], None]: The current round number and Challenge, or None if no round is active.
    """
    with self.__lock:
      if self.__current_round == None:
        return None
      return self.__current_round, self.__rounds[self.__current_round]


  def handle_submission(self, user: User, content: str) -> Union[SubmissionType, None]:
    """
      Processes a submission from a user, updating the internal submissions store.

      Args:
        user (User): The user submitting the content.
        content (str): The content of the submission.

      Returns:
        Union[SubmissionType, None]: The role of the user in the current round, or None if the round is 
                                     not active or the user is not part of a team.
    """
    if not self.current_round_is_active() or user.team is None:
      return None

    if not self.__submissions.contains(user.team.id):
      self.__submissions.set(user.team.id, {})

    with self.__lock:
      role = self.retrieve_role(user.retrieve_number())
      logger.submission(self.__current_round, user.team.id, role.value, content)

    self.__submissions.update_dict_value(user.team.id, role, content)
    return role


  def round_end_time(self) -> Union[datetime, None]:
    """
      Calculates the end time of the current round.

      Returns:
        Union[datetime, None]: The end time of the current round, or None if no round is active.
    """
    if self.__current_round == None:
      return None
    return int(datetime.fromtimestamp(self.__current_round_start + self.__round_duration, timezone.utc).timestamp())


  def get_submission(user: User) -> Tuple[str, str]:
    """
      Retrieves the submission for a given user.

      Args:
        user (User): The user for which to retrieve the submission.

      Returns:
        Tuple[str, str]: The CSS and HTML submissions for the user.
    """
    if user.team is None:
      return '', ''
    return self.__get_submission(user.team.id)


  def __get_submission(self, team_id: int) -> Tuple[str, str]:
    """
      Internal method to fetch submissions for a specific team.

      Args:
        team_id (int): The ID of the team for which to retrieve submissions.

      Returns:
        Tuple[str, str]: The CSS and HTML submissions for the team.
    """
    html = self.__submissions.get(team_id, {}).get(SubmissionType.HTML, '')
    css = self.__submissions.get(team_id, {}).get(SubmissionType.CSS, '')
    return html, css


  def __next(self) -> Union[int, None]:
    """
      Advances to the next round, updating the round index and start time.

      Returns:
        Union[int, None]: The index of the next round, or None if there are no more rounds.
    """
    with self.__lock:
      if self.__current_round is not None and self.__current_round >= len(self.__rounds) - 1:
        return None

      if self.__current_round == None:
        self.__current_round = 0
        self.__current_round_start = time.time()
      else:
        self.__current_round_start = self.round_end_time() + self.__break_duration
        self.__current_round += 1
      
      return self.__rounds[self.__current_round]


  def __run(self) -> None:
    """
      The main loop for managing rounds, responsible for transitioning between rounds and 
      handling end-of-round events.

      When a round ends, the submissions are persisted to the database and the next round
      is started.

      At the start of each round, the challenge is broadcasted to all connected clients.
      After the round ends, the end time is broadcasted to all connected clients.
    """
    while self.__is_running:
      if self.current_round_is_active():
        eventlet.sleep(1)
        continue

      with self.__lock:
        end_time = self.round_end_time()
      self.__socket.emit('round_end', { 'end': end_time + self.__break_duration if end_time else None })


      need_sleep = False
      with self.__lock:
        if self.__current_round is not None:
          copy = self.__submissions.copy()
          eventlet.spawn(persist_sumbissions, self.__current_round, copy)
          self.__submissions.clear()
          need_sleep = True
      
      if need_sleep:
        eventlet.sleep(self.__break_duration)

      next_round = self.__next()
      if next_round is None:
        break

      current = self.current()
      if current is not None:
        _, challenge = current
        challenge = challenge.to_dict()
        self.__socket.emit('round_start', { 'round': challenge, 'end': self.round_end_time() })



round_manager = RoundManager()