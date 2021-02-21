from UnleashClient.strategies import Strategy

class EnableForExperts(Strategy):
    def load_provisioning(self) -> list:
        return [x.strip() for x in self.parameters["expertEmails"].split(',')]

    def apply(self, context: dict = None) -> bool:
        """
        Check if feature is enabled for expert or not
        
        Args:
            context(dict): expert email provided as context
        """
        default_value = False

        if "expertEmails" in context.keys():
            default_value = context["expertEmails"] in self.parsed_provisioning

        return default_value
