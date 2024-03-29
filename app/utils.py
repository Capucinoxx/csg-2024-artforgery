# Description:  This file contains the utility functions and classes used in the application.
# Path:         app/utils.py
# Author:       Capucinoxx
# Date:         2024

import csv
import logging
import re
from typing import Any

import eventlet
import numpy as np
from bs4 import BeautifulSoup
from eventlet.semaphore import Semaphore

from app.cmd.app import app


def cleanup_html(html: str) -> str:
  """
    Removes unnecessary tags and attributes from the provided HTML content.

    List of tags to remove:
    ['script', 'iframe', 'link', 'img', 'style', 'embed', 'object']

    List of attributes to remove:
    ['style', 'background', 'src', 'href']

    Args:
      html (str): The HTML content to clean.

    Returns:
      str: The cleaned HTML content.
  """
  soup = BeautifulSoup(html, 'lxml')

  tags_to_remove = ['script', 'iframe', 'link', 'img', 'style', 'embed', 'object']
  for tag in tags_to_remove:
    for elem in soup.find_all(tag):
      elem.decompose()

  attributes_to_remove = ['style', 'background', 'src', 'href']
  for tag in soup.find_all():
    for attr in attributes_to_remove:
      del tag[attr]

  if soup.body:
    return ''.join(str(tag) for tag in soup.body.contents)
  else:
    return str(soup)



def cleanup_css(css: str) -> str:
  """
    Cleans up the provided CSS content by removing imports, URLs, and expressions.

    Args:
      css (str): The CSS content to clean.

    Returns:
      str: The cleaned CSS content.
  """
  soup = BeautifulSoup(css, "lxml")
  cleaned_css = soup.get_text()
    
  cleaned_css = re.sub(r'(?i)@import.*?;', '', cleaned_css)
  cleaned_css = re.sub(r'(?i)url\(.*?\)', '', cleaned_css)
  cleaned_css = re.sub(r'(?i)expression\(.*?\)', '', cleaned_css)

  return cleaned_css



def execute_with_timeout(func, *args, timeout: int = 1) -> Any:
  """
    Executes a function with a specified timeout.

    Args:
      func: The function to execute.
      *args: Arguments to pass to the function.
      timeout (int): The timeout in seconds.

    Returns:
      Any: The result of the function or None if the timeout is exceeded.
  """
  with eventlet.Timeout(timeout, False):
    return func(*args)
  return None



class CDict:
  """
    A thread-safe dictionary with basic CRUD operations.
  """
  def __init__(self):
    self.__data = {}
    self.__lock = Semaphore()


  def get(self, key: str, default: Any = None) -> Any:
    """
      Retrieves a value from the dictionary, returning a default if the key is not found.

      Args:
        key (str): The key to look up.
        default (Any): The default value to return if the key is not found.

      Returns:
        Any: The value associated with the key or the default value.
    """
    with self.__lock:
      return self.__data.get(key, default)


  def set(self, key: str, value: Any) -> None:
    """
      Sets the value for a key in the dictionary.

      Args:
        key (str): The key for the value.
        value (Any): The value to set.
    """
    with self.__lock:
      self.__data[key] = value


  def items(self) -> list:
    """
      Returns a list of key-value pairs in the dictionary.

      Returns:
        list: The key-value pairs in the dictionary.
    """
    with self.__lock:
      return list(self.__data.items())


  def copy(self) -> dict:
    """
      Returns a copy of the dictionary.

      Returns:
        dict: A copy of the dictionary.
    """
    with self.__lock:
      return self.__data.copy()


  def clear(self) -> None:
    """
      Clears all items from the dictionary.
    """
    with self.__lock:
      self.__data.clear()


  def contains(self, key: str) -> bool:
    """
      Checks if a key exists in the dictionary.

      Args:
        key (str): The key to check.

      Returns:
        bool: True if the key exists, False otherwise.
    """
    with self.__lock:
      return key in self.__data


  def update_dict_value(self, key: str, subkey: str, value: Any) -> None:
    """
      Updates a value in a nested dictionary structure within the CDict instance.

      Args:
        key (str): The main key in the dictionary to access the nested dictionary.
        subkey (str): The key within the nested dictionary where the value will be updated or set.
        value (Any): The value to set at the specified nested key.

      Note: If the main key does not exist, a new nested dictionary will be created.
    """
    with self.__lock:
      if key not in self.__data:
        self.__data[key] = {}
      self.__data[key][subkey] = value



class Logger:
  """
    A thread-safe logger that logs messages to both the console and a file.
  """
  def __init__(self, name: str, filename: str):
    self.__lock = Semaphore() 

    self.__logger = logging.getLogger(name)
    self.__logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    self.__logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(filename, mode='a')
    file_handler.setFormatter(formatter)
    self.__logger.addHandler(file_handler)

    
  def submission(self, round_id: int, team_id: int, role: str, message: str) -> None:
    """
      Logs a formatted submission message.

      Args:
        round_id (int): The round identifier.
        team_id (int): The team identifier.
        role (str): The role associated with the message.
        message (str): The message to log.
    """
    message = message.replace('\n', '\\n').replace('\r', '\\r')
    with self.__lock:
      self.__logger.info(f'[{round_id}{team_id}] {role}: {message}')

    
    def log(self, message: str) -> None:
      """
        Logs a message.

        Args:
          message (str): The message to log.
      """
      with self.__lock:
        self.__logger.info(message)



def consum_creds(path: str) -> dict:
  """
    Reads credentials from a CSV file and structures them into a dictionary.

    Args:
      path (str): The file path of the CSV file containing the credentials.

    Returns:
      dict: A dictionary with equipment names as keys and a list of tuples (username, password) as values.
  """
  d = {}
  try:
    with open(path, encoding='utf-8', mode='r') as f:
      data = csv.reader(f)
      next(data)

      for line in data:
        _, equip, password = line

        if equip not in d:
          d[equip] = []

        d[equip].append((f"{equip}_1", password))
        d[equip].append((f"{equip}_2", password))
  finally:
    return d



logger = Logger('round_manager', app.config.get('LOG_FILE', 'round_manager.log'))
