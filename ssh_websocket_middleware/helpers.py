import obsws_python as obs

client = obs.ReqClient(host="127.0.0.1", port=4455, password="aE5JQtDAWqDR2Jok")


scene_names = [
    "MAIN_LIVE",
    "SOCIAL_MEDIA_BOTTOM_LEFT",
    "TYPEWRITER",
    "LAST_TRACKS"
]

for scene_name in scene_names:
    resp = client.get_scene_item_list(name=scene_name)
    print(f"---\nScene: {scene_name}")
    for item in resp.scene_items:
        print(item["sourceName"], item["sceneItemId"])