from UnleashClient.strategies import Strategy

class EnableForDomains(Strategy):
    def load_provisioning(self) -> list:
        return [x.strip() for x in self.parameters["domain_names"].split(',')]

    def apply(self, context: dict = None) -> bool:
        """
        Check if feature is enabled for given domain_name or not
        
        Args:
            context(dict): domain_name provided as context
        """
        default_value = False

        if "domain_names" in context.keys():
            default_value = context["domain_names"] in self.parsed_provisioning

        return default_value
