from zero_mq import ZMQReq


class ExampleRequest(ZMQReq):
    """
    An example request to use as a more detailed template.
    """
    def __init__(self):
        """
        Instantiate desired class variables.
        """
        self.success = False
        self.response = {'results': None, 'failures': list()}

    def process_requests(self, message=None):
        """
        Do the actual work requested.

        :param message: The message as assembled by the client.
        :type messge: dict
        :return: The result of the work, in this case, some sums.
        :rtype: dict
        """
        # Set the message to something that looks like it would come from ZMQClient.
        # This should be supplied by the client, this is just for this example and
        # shouldn't have to be created in this method in an actual application.
        self.message = message if message is not None else {
            'requests': ['test', 'strings', 4],
            'uuid': 11111111-2222-3333-4444-555555555555,
            'all_or_none': True,
            'retries': 3
        }

        # "reqs" is a list for pipelining. Even single requests should be wrapped
        # in a list for consistency.
        for req in self.message.get('requests'):
            req_result = self.handle_request(req)

            # If we hit a failure and we want all or none, no reason to keep operating
            # on the rest of the items in the pipeline.
            if self.message.get('all_or_none') and not req_result:
                break

        # Deal with the validation and rollback if required.
        if False in set(self.results):
            if self.message.get('all_or_none'):
                self.rollback()
        else:
            self.success = True

        # This is Python 3.5 syntax. Use old style .update if using earlier 3.x.
        return {**self.response, **self.message, **{'success': self.success}}

    def handle_request(self, req):
        """
        Handle processing a single request.

        :param req: The request. This can be anything, it's supplied to the client and passed on.
        :type req: object
        """
        # Attempt to do the actual work. In this case, we are just trying to capitalize.
        for attempt in range(self.message.get('retries')):
            try:
                self.response.get('results').append(req.capitalize())
                outcome = True
                break

            # This could handle exceptions or raise them, depending on desired effect.
            except:
                self.response.get('results').append(False)
                self.response.get('failures').append(req)
                outcome = False

            finally:
                return outcome

    def rollback(self):
        """
        Handle rollback of the requests.
        """
        # In this case, we are just returning the original strings, but in actual application,
        # this will need to actively undo whatever was done.
        self.results = self.message.get('requests')
