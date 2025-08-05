class ResponseGenerated:
    def __init__(self, response: str):
        self.response = response

    def __str__(self):
        return f"ResponseGenerated(response={self.response})"
