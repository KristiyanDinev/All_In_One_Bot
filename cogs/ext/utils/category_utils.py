from cogs.ext.imports import *


async def editCategory(category: discord.CategoryChannel, categoryData: dict) -> bool:
    try:
        position: int = categoryData.get("position")
        if not isinstance(position, int):
            position = category.position
        permissions = categoryData.get("permissions")
        if isinstance(permissions, dict):
            await category.edit(reason=str(categoryData.get("reason", "")), name=str(categoryData.get("new_name", "")),
                                position=position, nsfw=bool(categoryData.get("nsfw", False)),
                                overwrites=getPermissionsMapping(permissions, category.guild))
        else:
            await category.edit(reason=str(categoryData.get("reason", "")), name=str(categoryData.get("new_name", "")),
                                position=position, nsfw=bool(categoryData.get("nsfw", False)))
        return True
    except Exception:
        return False


def getCategories(categoryData: dict, guild: discord.Guild) -> List[None] | list:
    categoryIds = categoryData.get("category_id")
    categoryNames = categoryData.get("category_name")
    if isinstance(categoryIds, int):
        categoryIds = [categoryIds]
    elif not isinstance(categoryIds, list):
        categoryIds = []

    if isinstance(categoryNames, str):
        categoryNames = [categoryNames]
    elif not isinstance(categoryNames, list):
        categoryNames = []

    categories: list = []
    for ids in categoryIds:
        for cat in guild.categories:
            if cat.id == ids:
                categories.append(cat)
    for name in categoryNames:
        for cat in guild.categories:
            if cat.name == name:
                categories.append(cat)
    if len(categories) == 0:
        return [None]
    return categories


async def createCategory(categoryData: dict, guild: discord.Guild) -> discord.CategoryChannel:
    position = categoryData.get("position")
    if not isinstance(position, int):
        position = 1
    permissions = categoryData.get("permissions")
    if not isinstance(permissions, dict):
        permissions = dict()
    return await guild.create_category(
        name=str(categoryData.get("name", "CategoryName")), position=position,
        reason=str(categoryData.get("reason", "")), overwrites=getPermissionsMapping(permissions, guild))


def getCategoryData(category: discord.CategoryChannel) -> dict:
    data: dict = dict()
    data["name"] = category.name
    data["id"] = category.id
    data["position"] = category.position
    data["created_at"] = category.created_at
    data["type"] = category.type.name
    data["jump_url"] = category.jump_url
    data["nsfw"] = category.is_nsfw()
    data["category_id"] = category.category_id
    data["permissions"] = getPermissionsDataFromMapping(category.overwrites)
    return data


async def deleteCategory(category: discord.CategoryChannel, reason: str = ""):
    await category.delete(reason=reason)
