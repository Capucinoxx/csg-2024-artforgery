# Description:  This file contains the routes and socket events used for handling user requests.
# Path:         app/routes.py
# Author:       Capucinoxx
# Date:         2024

import random
from functools import wraps
from typing import List, Callable, Any

from flask import jsonify, redirect, request, render_template, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room

from app.cmd.app import app
from app.database import db
from app.models import User, Challenge, SubmissionType, Submission
from app.round_manager import round_manager
from app.utils import cleanup_html, cleanup_css


# Initialize the login manager and associate it with the app
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

socketio = SocketIO(async_mode='eventlet')


@login_manager.user_loader
def load_user(user_id: int) -> User:
  """
    Callback function used by Flask-Login to load a user from the database.
    
    Args:
      user_id (int): The ID of the user to load.
    
    Returns:
      User: The user object if found, otherwise None.
  """
  return User.objects(pk=user_id).first()



def admin_required(func: Callable) -> Callable:
  """
    Decorator that ensures the user is authenticated and an admin to access a route.

    Args:
      func (Callable): The function to wrap.
    
    Returns:
      Callable: The wrapped function.
  """
  @wraps(func)
  def wrapper(*args: Any, **kwargs: Any) -> Any:
    if not current_user.is_authenticated or not current_user.is_admin:
      return jsonify({'error': 'Unauthorized'}), 401
    return func(*args, **kwargs)
  return wrapper



def form_required(fields: List[str]) -> Callable:
  """
    Decorator that ensures specific form fields are provided in a request.

    Args:
      fields (List[str]): List of required form field names.
    
    Returns:
      Callable: The decorated function.
  """
  def decorator(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
      if request.method == 'GET':
        return func(*args, **kwargs)
      for field in fields:
        if field not in request.form:
          return jsonify({'error': f'{field} is required'}), 400
      return func(*args, **kwargs)
    return wrapper
  return decorator



@app.route('/login', methods=['GET', 'POST'])
@form_required(['username', 'password'])
def login() -> Any:
  """
    Handles the login process. If the user is authenticated, redirects to the index page.
    If the method is GET, renders the login template. On POST, validates the user credentials.
    
    Returns:
        Any: The response or rendered template.
  """
  if current_user.is_authenticated:
    return redirect(url_for('index'))

  if request.method == 'GET':
    return render_template('login.html')

  username = request.form['username']
  password = request.form['password']

  user = User.objects(username=username).first()
  if user is None or not user.check_password(password):
      return render_template('login.html')

  login_user(user)
  return redirect(url_for('index'))



@app.route('/logout')
def logout() -> Any:
  """
    Logs out the current user and redirects to the login page.

    Returns:
      Any: Redirection to the login page.
    """
  logout_user()
  return redirect(url_for('login'))



@app.route('/')
@login_required
def index() -> Any:
  """
    The index page which shows different content based on whether the user is an admin or not.
    
    Returns:
      Any: The rendered template for the index page.
    """
  if current_user.is_admin:
    return render_template('admin.html',  users=User.objects().all(), 
                                          challenges=[c.to_dict() for c in Challenge.objects().all()],
                                          time_left=round_manager.round_end_time(),
                                          current_round=round_manager.current(),
                                          submissions=[s.to_dict() for s in Submission.objects().all()])

  return render_template('index.html',  time_left=round_manager.round_end_time(), 
                                        current_round=round_manager.current() if round_manager.current_round_is_active() else None,
                                        role=round_manager.retrieve_role(current_user.retrieve_number()).value)



@app.route('/admin/start')
@admin_required
def start() -> Any:
  """
    Admin route to start a round. Returns a success JSON response.

    Returns:
      Any: JSON response indicating success.
  """
  round_manager.start()
  return jsonify({'success': True}), 200



@socketio.on('connect')
@login_required
def connect() -> None:
  """
    Handles a client's connection event. When a user connects, they are added to a room
    based on their team ID, allowing for targeted broadcasting.

    Requires the user to be authenticated.
  """
  join_room(str(current_user.team.id))



@socketio.on('disconnect')
@login_required
def disconnect() -> None:
  """
    Handles a client's disconnect event. When a user disconnects, they are removed from
    their team's room.

    Requires the user to be authenticated.
  """
  leave_room(str(current_user.team.id))


@socketio.on('sync')
@login_required
def handle_message(code: str) -> None:
  """
    Handles the 'sync' event from the client, which is triggered when there is data
    (specifically, code in this context) that needs to be synchronized with other team members.

    Args:
      code (str): The code snippet or content that needs to be synchronized.

    This function checks if the current round is active, processes the code based on the user's
    submission type (HTML or CSS), cleans it if necessary, and then emits an 'update' event
    to the user's team room with the processed code.

    Additionally, there's a random chance to trigger a 'leak' event, broadcasting the code
    to all connected clients.
  """
  if round_manager.current_round_is_active():
    if code is None:
      code = ''

    role = round_manager.handle_submission(current_user, code)

    if role == SubmissionType.HTML:
      code = cleanup_html(code)
    elif role == SubmissionType.CSS:
      code = cleanup_css(code)

    if role is not None:
      emit('update', {'role': role.value, 'code': code}, room=str(current_user.team.id))

      # Randomly trigger a 'leak' event to simulate a unexpected data leak broadcast
      if random.randint(0, 100) < 10:
        socketio.emit('leak', {'code': code})
