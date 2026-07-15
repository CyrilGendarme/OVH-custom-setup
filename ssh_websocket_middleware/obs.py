import obsws_python as obs


class OBSController:
    def __init__(self, config):
        config = config.get("obs", {})

        self.host = config.get("host", "127.0.0.1")
        self.port = config.get("port", 4455)
        self.password = config.get("password", "")

        self.client = obs.ReqClient(
            host=self.host,
            port=self.port,
            password=self.password
        )
        
    def get_scene_name(self):
        try:
            response = self.client.get_current_program_scene()
            return response.scene_name
        except Exception as exc:
            print(f"OBS get scene name failed: {exc}")
            return None

    def activate_macro(self, macro_name):
        try:
            if macro_name == "Typerwriter":
                self.client.trigger_hot_key_by_name("macro_condition_hotkey_Macro trigger hotkey 1")
            elif macro_name == "Social Media":
                self.client.trigger_hot_key_by_name("macro_condition_hotkey_Macro trigger hotkey 2")
       
        except Exception as exc:
            print(f"OBS macro failed: {exc}")