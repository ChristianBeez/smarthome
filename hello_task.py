#!/usr/bin/env python3
"""Scheduled task: prints 'hallo' at 03:30 every day."""

from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

if __name__ == '__main__':
    logging.info('hallo')
