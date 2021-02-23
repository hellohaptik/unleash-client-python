from UnleashClient.strategies import Strategy

class EnableForBusinesses(Strategy):
    def load_provisioning(self) -> list:
        return [
            x.strip() for x in self.parameters["business_via_names"].split(',')
        ]

    def apply(self, context: dict = None) -> bool:
        """
        Check if feature is enabled for given business or not
        
        Args:
            context(dict): business-via-name provided as context
        """
        default_value = False

        if "business_via_names" in context.keys():
            default_value = context["business_via_names"] in self.parsed_provisioning

        return default_value