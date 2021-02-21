from UnleashClient.strategies import Strategy

class EnableForDomains(Strategy):
    def load_provisioning(self) -> list:
        return [x.strip() for x in self.parameters["domainNames"].split(',')]

    def apply(self, context: dict = None) -> bool:
        """
        Turn on if I'm a cat.

        :return:
        """
        default_value = False

        if "domainNames" in context.keys():
            default_value = context["domainNames"] in self.parsed_provisioning

        return default_value
