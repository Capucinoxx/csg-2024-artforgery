from app.cmd.app import app

from app.database import db
from app.models import seed_users, seed_challenges
from app.routes import socketio
from app.round_manager import round_manager
from app.utils import consum_creds

import logging


try:
  db.init_app(app)
  round_manager.init_app(app, socketio)
  seed_challenges()
  seed_users(consum_creds('app/creds.csv'))


  socketio.init_app(app, async_mode='eventlet')
  socketio.run(app, host='0.0.0.0', port=5000, debug=True)
except KeyboardInterrupt:
  round_manager.stop()
  socketio.stop()
  exit(0)