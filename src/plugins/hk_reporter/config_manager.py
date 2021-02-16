from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Bot, Event, GroupMessageEvent
from nonebot.permission import Permission, SUPERUSER
from nonebot.adapters.cqhttp.permission import GROUP_ADMIN, GROUP_MEMBER, GROUP_OWNER
from nonebot import on_command, logger

from .platform.utils import check_sub_target
from .platform import platform_manager
from .config import Config, NoSuchSubscribeException
from .utils import parse_text
from .send import send_msgs

add_sub = on_command("添加订阅", rule=to_me(), permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER, priority=5)
@add_sub.got('platform', '请输入想要订阅的平台，目前支持：{}'.format(', '.join(platform_manager.keys())))
@add_sub.got('id', '请输入订阅用户的id，详情查阅https://github.com/felinae98/nonebot-hk-reporter')
@add_sub.handle()
async def add_sub_handle_id(bot: Bot, event: Event, state: T_State):
    if 'id' in state:
        return
    await bot.send(event=event, message='请输入订阅用户的id，详情查阅https://github.com/felinae98/nonebot-hk-reporter')
    await add_sub.pause()

@add_sub.handle()
async def add_sub_parse_id(bot: Bot, event: Event, state: T_State):
    if 'id' in state:
        return
    target = str(event.get_message()).strip()
    name = await check_sub_target(state['platform'], target)
    if not name:
        await add_sub.reject('id输入错误')
    state['id'] = target
    state['name'] = name

async def add_sub_handle_cat(bot: Bot, event: Event, state: T_State):
    if not platform_manager[state['platform']].categories:
        return
    if 'cats' in state:
        return
    msg = '请输入要订阅的类别，以空格分隔，支持的类别有：{}'.format(
            ','.join(list(platform_manager[state['platform']].categories.values()))
        )
    logger.debug('send' + msg)
    await bot.send(event=event, message=msg)
    await add_sub.pause()

@add_sub.handle()
async def add_sub_parse_cat(bot: Bot, event: Event, state: T_State):
    if not platform_manager[state['platform']].categories:
        return
    if 'cats' in state:
        return
    res = []
    for cat in str(event.get_message()).strip().split():
        if cat not in platform_manager[state['platform']].reverse_category:
            await add_sub.reject('不支持 {}'.format(cat))
            res.append(platform_manager[state['platform']].reverse_category[cat])
    state['cat'] = res

@add_sub.handle()
async def add_sub_handle_tag(bot: Bot, event: Event, state: T_State):
    if not platform_manager[state['platform']].enable_tag:
        return
    if 'tags' in state:
        return
    await bot.send(event=event, message='请输入要订阅的tag，订阅所有tag输入"全部标签"')
    await add_sub.pause()

@add_sub.handle()
async def add_sub_parse_tag(bot: Bot, event: Event, state: T_State):
    if not platform_manager[state['platform']].enable_tag:
        return
    if 'tags' in state:
        return
    if str(event.get_message()).strip() == '全部标签':
        state['tags'] = []
    else:
        state['tags'] = str(event.get_message()).strip().split()

@add_sub.handle()
async def add_sub_process(bot: Bot, event: Event, state: T_State):
    config = Config()
    config.add_subscribe(event.group_id, user_type='group', target=state['id'],
            target_name=state['name'], target_type=state['platform'],
            cats=state.get('cats', []), tags=state.get('tags', []))
    await add_sub.finish('添加 {} 成功'.format(state['name']))
    

# @add_sub.handle()
# async def _(bot: Bot, event: Event, state: T_State):
#     args = str(event.get_message()).strip().split()
#     if len(args) != 2:
#         await add_sub.finish("使用方法为： 添加订阅 平台 id")
#         return
#     target_type, target = args
#     if name := await check_sub_target(target_type, target):
#         config: Config = Config()
#         config.add_subscribe(event.group_id, "group", target, name, target_type)
#         await add_sub.finish("成功添加 {}".format(name))
#     else:
#         await add_sub.finish("平台或者id不存在")
    
query_sub = on_command("查询订阅", rule=to_me(), priority=5)
@query_sub.handle()
async def _(bot: Bot, event: Event, state: T_State):
    config: Config = Config()
    sub_list = config.list_subscribe(event.group_id, "group")
    res = '订阅的帐号为：\n'
    for sub in sub_list:
        res += '{} {} {}\n'.format(sub['target_type'], sub['target_name'], sub['target'])
    send_msgs(bot, event.group_id, 'group', [await parse_text(res)])
    await query_sub.finish()

del_sub = on_command("删除订阅", rule=to_me(), permission=GROUP_ADMIN | GROUP_OWNER, priority=5)
@del_sub.handle()
async def _(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip().split()
    if len(args) != 2:
        await del_sub.finish("使用方法为： 删除订阅 平台 id")
        return
    target_type, target = args
    config = Config()
    try:
        config.del_subscribe(event.group_id, "group", target, target_type)
    except NoSuchSubscribeException:
        await del_sub.finish('平台或id不存在')
    await del_sub.finish('删除成功')

