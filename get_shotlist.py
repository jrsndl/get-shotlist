import nuke
import ayon_api
import csv
import os


def attribs_to_columns(a):
    fin = int(a["frameStart"]) - int(a["handleStart"])
    fout = int(a["frameEnd"]) - int(a["handleEnd"])
    d = {
        "Range": f"{fin}-{fout}",
        "Length": str(fout - fin + 1),
        "In": str(a["frameStart"]),
        "Out": str(a["frameEnd"]),
        "Head": str(a["handleStart"]),
        "Tail": str(a["handleEnd"]),
        "Width": str(a["resolutionWidth"]),
        "Height": str(a["resolutionHeight"]),
        "Pixel Aspect": str(a["pixelAspect"]),
        "Clip In": str(a["clipIn"]),
        "Clip Out": str(a["clipOut"]),
    }
    return d


def get_shotlist():
    columns = [
        "Thumbnail",
        "Folder Name",
        "Folder Path",
        "Folder Type",
        "Task Type",
        "Task Name",
        "Task Assignees",
        "Range",
        "Length",
        "In",
        "Out",
        "Head",
        "Tail",
        "Width",
        "Height",
        "Pixel Aspect",
        "Clip In",
        "Clip Out",
        "Folder Label",
        "Folder Status",
        "Task Label",
        "Task Status",
        ]

    task_empty = {
        "Task Type": "",
        "Task Name": "",
        "Task Label": "",
        "Task Status": "",
        "Task Assignees": ""
    }
    p = nuke.Panel("Create Shot List Spreadsheet from Ayon")
    p.addFilenameSearch("Pick a Folder:", 'd:/shotlist')
    _result = p.show()
    script_base_dir = p.value("Pick a Folder:")

    # paths
    thumbs_dir = f"{script_base_dir}/_thumbsDownload"
    os.makedirs(thumbs_dir, exist_ok=True)
    output_path = f"{script_base_dir}/shots.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # context
    prj = os.environ.get("AYON_PROJECT_NAME")

    # get folders
    asset_entities = ayon_api.get_folders(prj, fields={"name", "id", "path", "type", "label", "status", "hasTasks", "attrib", 'thumbnailId'})
    asset_entities = {f["name"]: f for f in asset_entities}

    # get folders + tasks and their attribs
    data = []
    for asset_name, asset in asset_entities.items():
        thumb_name_folder = asset["path"].replace("/", "-").strip("-")
        thumbnail_path = None
        if asset["thumbnailId"] is not None:
            thumbnail = ayon_api.get_thumbnail_by_id(prj, asset["thumbnailId"])
            thumbnail_path = f"{thumbs_dir}/{thumb_name_folder}.png"
            with open(thumbnail_path, "wb") as stream:
                stream.write(thumbnail.content)
            if not os.path.isfile(thumbnail_path):
                thumbnail_path = None

        base = {
            "Thumbnail": thumbnail_path,
            "Folder Type": asset["type"],
            "Folder Name": asset_name,
            "Folder Path": asset["path"],
            "Folder Label": asset["label"],
            "Folder Status": asset["label"],
        }
        shot_clean = base | attribs_to_columns(asset["attrib"])
        shot_only = shot_clean | task_empty
        data.append(shot_only)

        if asset["hasTasks"]:
            task_entities = ayon_api.get_tasks(prj, folder_ids={asset["id"]},
                                               fields={"name",
                                                       "id",
                                                       "type",
                                                       "label",
                                                       "assignees",
                                                       "status",
                                                       "attrib",
                                                       'thumbnailId'})
            task_entities = {f["name"]: f for f in task_entities}
            for task_name, task_info in task_entities.items():
                thumb_name_task = thumb_name_folder + "-task-" + task_name
                thumbnail_path = None
                if task_info["thumbnailId"] is not None:
                    thumbnail = ayon_api.get_thumbnail_by_id(
                        prj, task_info["thumbnailId"])
                    thumbnail_path = f"{thumbs_dir}/{thumb_name_task}.png"
                    with open(thumbnail_path, "wb") as stream:
                        stream.write(thumbnail.content)
                    if not os.path.isfile(thumbnail_path):
                        thumbnail_path = None
                tsk = {
                    "Task Type": task_info["type"],
                    "Task Name": task_info["name"],
                    "Task Label": task_info["label"],
                    "Task Status": task_info["status"],
                    "Task Assignees": " ".join(task_info["assignees"])
                }
                shot_task = shot_clean | tsk
                shot_task["Folder Type"] = f'{shot_task["Folder Type"]}/Task'
                shot_task_attr = shot_task | attribs_to_columns(
                    task_info["attrib"])
                data.append(shot_task_attr)
    sorted_data = sorted(data, key=lambda d: d['Folder Path'])

    with open(output_path, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, columns)
        dict_writer.writeheader()
        dict_writer.writerows(sorted_data)

    nuke.message(f"Shot List exported to {output_path}")
