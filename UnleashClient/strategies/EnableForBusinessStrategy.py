from UnleashClient.strategies import Strategy

class EnableForBusinesses(Strategy):
    def load_provisioning(self) -> list:
        return [
            x.strip() for x in self.parameters["businessViaNames"].split(',')
        ]

    def apply(self, context: dict = None) -> bool:
        """
        Check if feature is enabled for given business or not
        
        Args:
            context(dict): business-via-name provided as context
        """
        default_value = False

        if "businessViaNames" in context.keys():
            default_value = context["businessViaNames"] in self.parsed_provisioning

        return default_value

