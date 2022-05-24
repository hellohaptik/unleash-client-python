from UnleashClient.strategies import Strategy


class EnableForTeams(Strategy):
    def load_provisioning(self) -> list:
        return [
            x.strip() for x in self.parameters["team_ids"].split(',')
        ]

    def apply(self, context: dict = None) -> bool:
        """
        Check if feature is enabled for given team or not
        
        Args:
            context(dict): team IDs provided as context
        """
        default_value = False

        if "team_ids" in context.keys():
            default_value = context["team_ids"] in self.parsed_provisioning

        return default_value
