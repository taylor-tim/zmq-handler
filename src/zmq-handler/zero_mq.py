#!/usr/bin/env python3


import json
import logging
import setproctitle
import zmq

from abc import ABCMeta
from argparse import ArgumentParser
from sys import argv, exit as sysexit
from uuid import uuid1 as uuid_gen


class ZMQBase(object):
    """
    The ZMQ base class for client or server.
    """

    def __init__(self, zmq_type='', proto='tcp', target='', port=3333):
        """
        :param zmq_type: Either 'zmq-server' or 'zmq-client'.
        :type zmq_type: str
        :param proto: The protocol to use.
        :type proto: str
        :param port: The port to use.
        :type port: int
        :param target: The target to use. For servers, IP to bind. For clients, IP of the server.
        :type target: str
        :return: A zmq socket to use.
        :rtype: zmq.Context.socket
        """
        if zmq_type not in {'server', 'client'}:
            raise ValueError('zmq_type must be either server or client. Supplied: {0}.'.format(zmq_type))

        if target == '':
            raise ValueError('You must specify a taget for bind/connect.')

        get_logger(name=zmq_type)
        context = zmq.Context()
        logging.info('Beginning %s config...' % zmq_type)

        if zmq_type == 'server':
            btype = 'bind'
            self.socket = context.socket(zmq.REP)

        elif zmq_type == 'client':
            btype = 'connect'
            self.socket = context.socket(zmq.REQ)

        getattr(self.socket, btype)('{0}://{1}:{2}'.format(proto, target, port))
        logging.info('ZMQ %s %sed %s to %s:%s' % (zmq_type, btype, proto, target, port))


class ZMQServer(ZMQBase):
    """
    ZMQ server class.
    """
    def start(self):

        try:
            while True:
                # Wait for incoming requests.
                message = self.socket.recv()
                logging.info('Received request %s' % message)

                # Perform actions on the request.
                # This is where the majority of work needs to be done.
                # Adjust response['result'] to be whatever you want to return.
                message = json.loads(message.decode())
                # Here is where you'd do work itself. Check ZMQReq and examples for help.
                # Placeholder here simply to not stack.
                response = {'result': "This is the result.", 'message': message}

                # Return response to client.
                logging.info('Sending response %s' % response)
                self.socket.send(json.dumps(response).encode())

        except KeyboardInterrupt:
            logging.info('Received interrupt, quitting...')

        finally:
            self.socket.close()
            sysexit(0)


class ZMQClient(ZMQBase):
    """
    ZMQ client class.
    """
    def __init__(self, proto='tcp', target='', port='3333'):
        """
        Initialize the client, using base as parent.

        :param proto: The protocol to use.
        :type proto: str
        :param port: The port to use.
        :type port: str
        :param target: The target to use. For REP, IP to bind. For REQ, IP of the server.
        :type target: str
        :return: A zmq socket to use.
        :rtype: zmq.Context.socket
        """
        super().__init__(zmq_type='client', proto=proto, target=target, port=port)

    def run_requests(self, reqs=None, all_or_none=False, retries=3):
        """
        Run the client.

        :param reqs: The requests to process.
        :type reqs: list
        :param all_or_none: Whether to process all requests despite failures or not.
        :type all_or_none: bool
        :param retries: Number of times to retry each request.
        :type retries: int
        :return: The results of the run along with the original message.
        :rtype: dict
        """
        if not isinstance(reqs, list):
            # Wrap a single req in a list, for compatibility with the ZMQServer.
            reqs = [reqs]

        req_uuid = str(uuid_gen())
        message = json.dumps({'requests': reqs, 'uuid': req_uuid, 'all_or_none': all_or_none, 'retries': retries})

        logging.info("Sending message %s …" % message)
        self.socket.send(message.encode())

        response = self.socket.recv()
        logging.info("Received reply %s [ %s ]" % (message, response))

        return json.loads(response.decode())


class ZMQReq(metaclass=ABCMeta):
    """
    The request object abstract base class.
    """
    def process_requests(self):
        # Do the actual work. This code should include some sort of error checking in order
        # to return to the client a valid or invalid operation. Best practice is always use
        # some error check, but is especially necessary for all_or_none to trigger rollbacks.
        pass

    def rollback(self):
        # Only really necessary to define work for all_or_none option.
        # If a pipelined set of requests are sent and all_or_none is True, then when any of the
        # set fails, the others will need a rollback method in order to undo what was done.
        pass


def get_logger(name=None, level='INFO', fmt='%Y.%m.%d-%H:%M:%S--'):
    """
    Get a logger object for use. Name determines filename.

    :param name: The name of the service, and what the file will be called.
    :type name: str
    :param level: The level to use.
    :type level: str
    :param fmt: Specific format if required.
    :type fmt: str
    """
    level = getattr(logging, level.upper())
    kwargs = {'level': level, 'format': '%(asctime)s %(levelname)s: %(message)s', 'datefmt': fmt}

    if name is not None:
        loc = '/var/log/zmq-{0}.log'.format(name)
        kwargs['filename'] = loc

    logging.basicConfig(**kwargs)


def main(arguments):

    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--client', action='store_true', default=False, help='Start ZMQ as a client')
    group.add_argument('-s', '--server', action='store_true', default=False, help="Start a ZMQ server.")
    server_group = group.add_argument_group('options')
    server_group.add_argument('-p', '--port', action='store', dest='port', default=3333, type=int,
                              help='Server: bind port. Client: Server port.')
    server_group.add_argument('-i', '--interface', action='store', dest='target', default='127.0.0.1', type=str,
                              help='Server: interface to bind to. Client: target IP to send request.')

    args = parser.parse_args(arguments)

    if args.server:
        setproctitle.setproctitle('zmq-server')
        zmq_server = ZMQServer(zmq_type='server', port=args.port, target=args.target)
        zmq_server.start()

    else:
        # You really shouldn't be running client from cli, this is mostly here
        # for testing purposes.
        setproctitle.setproctitle('zmq-client')
        zmq_client = ZMQClient(zmq_type='client', port=args.port, target=args.target)
        zmq_client.run_request()


if __name__ == '__main__':
    main(argv[1:])
