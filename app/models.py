# Description: This file contains the models used in the application.
# Path:        app/models.py
# Author:      Capucinoxx
# Date:        2024

import base64
import os
from datetime import datetime
from enum import Enum

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.cmd.app import app
from app.cmd.config import IMAGES_FOLDER
from app.database import db


class SubmissionType(Enum):
  """
    Enum class used to represent the type of submission.
  
    Attributes:
      HTML (str): The HTML submission type.
      CSS (str): The CSS submission type.
  """
  HTML = 'html'
  CSS = 'css'



class User(UserMixin, db.Document):
  """
    Class used to represent a user in the application.
  """
  meta = {'collection': 'users'}
  
  _id_in_team = db.IntField(required=True)
  username    = db.StringField(max_length=100, required=True, unique=True)
  password    = db.StringField(max_length=100, required=True)
  is_admin    = db.BooleanField(default=False)
  team        = db.ReferenceField('Team')


  def __repr__(self) -> str:
    return f'<User: {self.username}>'

    
  def get_id(self) -> str:
    return str(self.id)

  def get_id_in_team(self) -> int:
    return self._id_in_team


  def set_password(self, password: str) -> None:
    self.password = generate_password_hash(password)


  def check_password(self, password: str) -> bool:
    return check_password_hash(self.password, password)


  def to_dict(self) -> dict:
    return {
      'id': str(self.id),
      'username': self.username,
      'is_admin': self.is_admin,
      'team_id': str(self.team.id) if self.team else None,
    }


  def retrieve_number(self) -> int:
    return self._id_in_team


  def save(self, *args, **kwargs):
    """
      Overrides the save method to set the ID in the team.
      
      Returns:
        User: The saved user.
    """
    self._id_in_team = self._id_in_team or self.__get_next_id()
    return super().save(*args, **kwargs)

    
  def __get_next_id(self) -> int:
    """
      Returns the next ID in the team.
      
      Returns:
        int: The next ID in the team.
    """
    last_user = User.objects(team=self.team).order_by('-_id_in_team').first()
    return last_user._id_in_team + 1 if last_user else 1



class Team(db.Document):
  """
    Class used to represent a team in the application.
    A team is a group of two users that work together.
  """
  meta = {'collection': 'teams'}

  name       = db.StringField(max_length=100, required=True, unique=True)
  members    = db.ListField(db.ReferenceField(User, reverse_delete_rule=db.PULL))


  def to_dict(self) -> dict:
    return {
      'id': str(self.id),
      'name': self.name,
      'members': [member.to_dict() for member in self.members],
    }



class Challenge(db.Document):
  """
    Class used to represent a challenge in the application.
    A challenge is an image that the teams must replicate using HTML and CSS.
  """
  meta = {'collection': 'challenges'}

  _id   = db.IntField(primary_key=True)
  name  = db.StringField(max_length=100, required=True, unique=True)
  image = db.BinaryField()


  def save(self, *args, **kwargs):
    self._id = self._id or self.__get_next_id()
    return super().save(*args, **kwargs)


  def __get_next_id(self) -> int:
    """
      Returns the next ID for a challenge.
      
      Returns:
        int: The next ID for a challenge.
    """
    last_challenge = Challenge.objects.order_by('-_id').first()
    return last_challenge._id + 1 if last_challenge else 1

    
  def to_dict(self) -> dict:
    return {
      'id': self._id,
      'name': self.name,
      'image': base64.b64encode(self.image).decode('utf-8'),
    }



class Submission(db.Document):
  """
    Class used to represent a submission in the application.
    When round ends, teams persist their HTML and CSS code to the database.
  """
  meta = {'collection': 'submissions'}

  team = db.ReferenceField(Team)
  round_number = db.IntField()
  html = db.StringField()
  css = db.StringField()
  timestamp = db.DateTimeField(default=datetime.now)


  def to_dict(self) -> dict:
    return {
      'team': self.team.to_dict(),
      'round_number': self.round_number,
      'html': self.html,
      'css': self.css,
      'timestamp': self.timestamp.isoformat(),
    }



def seed_challenges():
  """
    Seeds the challenges in the database.
    Reads the images from the images folder and saves them as challenges.
  """
  for image in sorted(os.listdir(IMAGES_FOLDER)):
    if image.endswith('.png'):
      image_name = image.split('.')[0]
      if Challenge.objects(name=image_name):
        continue

      with open(f'{IMAGES_FOLDER}/{image}', 'rb') as f:
        challenge = Challenge(name=image_name, image=f.read())
        challenge.save()



def seed_users(data):
  """
    Seeds the users in the database.
    Reads the users from the data dictionary and saves them as users.
  """
  for name, users in data.items():
    if Team.objects(name=name):
      continue
    team = Team(name=name)
    team.save()

    for u in users:
      user = User(username=u[0], team=team)
      user.set_password(u[1])
      user.save()

        
    team_users = User.objects(team=team)
    team.members = list(team_users)
    team.save()

  if not User.objects(username='admin'):
    admin = User(username='admin')
    admin.set_password('SUPER_STRONG_PASSWORD')
    admin.is_admin = True
    admin.save()



def persist_sumbissions(round_number: int, data: dict):
  """
    Persists the submissions in the database.
  """
  app.logger.warning(f'Persisting submissions for round {round_number} {data}')

  for team in Team.objects():
    if not team:
      continue

    html = data.get(team.id, {}).get(SubmissionType.HTML, '')
    css = data.get(team.id, {}).get(SubmissionType.CSS, '')

    app.logger.warning(f'Persisting submission for {team.id} - {round_number} - {html} - {css}')

    submission = Submission(team=team, round_number=round_number, html=html, css=css)        
    submission.save()