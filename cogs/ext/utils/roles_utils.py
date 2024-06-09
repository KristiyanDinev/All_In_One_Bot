from cogs.ext.imports import *

async def createRole(roleData: dict, guild: discord.Guild) -> discord.Role:
    if "ROLE_ICONS" in guild.features:
        role: discord.Role = await guild.create_role(reason=roleData.get("reason", ""),
                                                     name=roleData.get("name", "No Name Given"),
                                                     display_icon=roleData.get("display_icon", ""),
                                                     color=getColour(str(roleData.get("color", "random"))),
                                                     mentionable=bool(roleData.get("mentionable", True)),
                                                     hoist=bool(roleData.get("hoist", True)),
                                                     permissions=getDiscordPermission(
                                                         dict(roleData.get("permissions", {}))))
    else:
        role: discord.Role = await guild.create_role(reason=roleData.get("reason", ""),
                                                     name=roleData.get("name", "No Name Given"),
                                                     color=getColour(str(roleData.get("color", "random"))),
                                                     mentionable=bool(roleData.get("mentionable", True)),
                                                     hoist=bool(roleData.get("hoist", True)),
                                                     permissions=getDiscordPermission(
                                                         dict(roleData.get("permissions", {}))))
    pos: str = str(roleData.get("position", ""))
    if pos.isdigit():
        await role.edit(position=int(pos))

    for user in getMembers(roleData, guild):
        await giveRoleToUser(user, role, str(roleData.get("give_reason", "")))
    return role


async def createRoleNoDisplayIcon(roleData: dict, guild: discord.Guild) -> discord.Role | None:
    try:
        role: discord.Role = await guild.create_role(reason=roleData.get("reason", ""),
                                                     name=roleData.get("name", "No Name Given"),
                                                     color=getColour(str(roleData.get("color", ""))),
                                                     mentionable=bool(roleData.get("mentionable", True)),
                                                     hoist=bool(roleData.get("hoist", True)),
                                                     permissions=getDiscordPermission(
                                                         dict(roleData.get("permissions", {}))))
        pos: str = str(roleData.get("position", ""))
        if pos.isdigit():
            await role.edit(position=int(pos))

        for user in getMembers(roleData, guild):
            await giveRoleToUser(user, role, str(roleData.get("give_reason", "")))
        return role
    except Exception:
        return None


async def deleteRole(role: discord.Role, reason: str):
    await role.delete(reason=reason)


def getRoles(roleData: dict, guild: discord.Guild) -> List[discord.Role]:
    try:
        roleId: str = str(roleData.get("role_id", ""))
        roleName: str = str(roleData.get("role_name", ""))
        roles = set()
        if roleId.isdigit():
            # search by id
            roles.add(guild.get_role(int(roleId)))

        if len(roleName.replace(" ", "")) > 0 and roleName != "@everyone":
            # search by name
            if roleName == "*":
                for r in guild.roles:
                    if r.name != "@everyone":
                        roles.add(r)
            else:
                for r in guild.roles:
                    if r.name != "@everyone" and r.name == roleName:
                        roles.add(r)
        return list(roles)
    except Exception:
        return []


def getPermissionData(role: discord.Role) -> dict:
    return {perm: getattr(role.permissions, perm)
            for perm, value in discord.Permissions.VALID_FLAGS.items()}


def getRoleData(role: discord.Role) -> dict:
    roleData = dict()
    roleData["name"] = role.name
    roleData["color"] = role.color
    roleData["display_icon"] = role.display_icon
    roleData["mentionable"] = role.mentionable
    roleData["hoist"] = role.hoist
    roleData["position"] = role.position
    roleData["permissions"] = getPermissionData(role)
    users = []
    for member in role.members:
        users.append(member.id)
    roleData["users"] = users
    return roleData


async def editRole(roleData: dict, role: discord.Role):
    position: str | None = str(roleData.get("position", None))
    reason: str = str(roleData.get("reason", ""))
    if not isinstance(position, int):
        position: int = role.position

    name: str = str(roleData.get("new_name", role.name))
    colour: discord.Colour = getColour(str(roleData.get("color", role.colour)))
    hoist: bool = bool(roleData.get("hoist", role.hoist))
    mentionable: bool = bool(bool(roleData.get("mentionable", role.mentionable)))
    permissions: discord.Permissions = getDiscordPermission(dict(roleData.get("permissions", {})))

    if "ROLE_ICONS" in role.guild.features:
        await role.edit(name=name, reason=reason, colour=colour, hoist=hoist, mentionable=mentionable,
                        position=position, permissions=permissions, display_icon=roleData.get("display_icon", None))

    else:
        await role.edit(name=name, reason=str(roleData.get("reason", "")), colour=colour, hoist=hoist,
                        mentionable=mentionable, position=position, permissions=permissions)

    if "users" in roleData.keys():
        users: list = roleData.get("users", [])
        if not isinstance(users, list):
            return
        for member in role.members:
            if member.id in users:
                continue
            await removeRole(member, role, reason=reason)

        for userId in users:
            member: discord.Member | None = getMemberGuild(role.guild, userId)
            if member is None or memberHasRole(member, role):
                continue
            await addRole(member, role, reason=reason)


def getRoleIdFromRoles(roles: List[discord.Role]) -> list:
    userRolesId = []
    for r in roles:
        if r.name == "@everyone":
            continue
        userRolesId.append(r.id)
    return userRolesId


def anyRolesContains(roles_id: list, roles_id2: list) -> bool:
    for role_id in roles_id:
        if role_id in roles_id2:
            return True
    return False


def allRolesContains(roles_id: list, roles_id2: list) -> bool:
    for role_id in roles_id:
        if role_id not in roles_id2:
            return False
    return True if len(roles_id) > 0 else False


def getRoleIdFromMention(roleMention: str) -> int:
    try:
        return int(roleMention.replace("<@&", "")[:-1]) if "<@" in roleMention else int(roleMention)
    except Exception:
        return 0


def getRole(interaction: discord.Interaction, roleId: int) -> None | discord.Role:
    if roleId == 0:
        return None
    return interaction.client.get_role(roleId)

