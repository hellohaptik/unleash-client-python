from UnleashClient.strategies import Strategy

class EnableForPartners(Strategy):
    def load_provisioning(self) -> list:
        return [
            x.strip() for x in self.parameters["partnerNames"].split(',')
        ]

    def apply(self, context: dict = None) -> bool:
        """
        Check if feature is enabled for given partner or not
        
        Args:
            context(dict): partner name provided as context
        """
        default_value = False

        if "partnerNames" in context.keys():
            default_value = context["partnerNames"] in self.parsed_provisioning

        return default_value

