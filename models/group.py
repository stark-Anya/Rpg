from database import groups_col


def default_group(group_id: int) -> dict:
    return {
        "group_id": group_id,
        "economy_open": True,
    }


async def get_group(group_id: int) -> dict:
    group = await groups_col.find_one({"group_id": group_id})
    if not group:
        group = default_group(group_id)
        await groups_col.insert_one(group)
    return group


async def set_economy(group_id: int, status: bool):
    await groups_col.update_one(
        {"group_id": group_id},
        {"$set": {"economy_open": status}},
        upsert=True
    )


async def is_economy_open(group_id: int) -> bool:
    group = await get_group(group_id)
    return group.get("economy_open", True)
