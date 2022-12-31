[🇷🇺 Russian](/README-RU.md)

Running in production:
<p float="left">
  <a title="VK" href="https://vk.com/ktmuslave">
    <img alt="VK" src="https://upload.wikimedia.org/wikipedia/commons/f/f3/VK_Compact_Logo_%282021-present%29.svg" width=35>
  </a>
  <a title="Telegram" href="https://t.me/ktmuslave_bot">
    <img alt="Telegram" src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" width=35>
  </a>
</p>

# KTMU slave
### A bot for schedule from https://ktmu-sutd.ru/

- Both for [VK](https://vk.com/ktmuslave) and [Telegram](https://t.me/ktmuslave_bot) with same codebase using custom generic handlers
- Easy step-by-step registration
- Easy paginated editable storage for each user for teachers' Zoom data to show it in schedule
- Broadcast on schedule change with detailed comparison, replying to the last message and optional pinning in chat
- Ability to force update schedule globally if someone noticed a change between the 10 min update period
- Miscellaneous useful links in schedule message: **original schedules**, **teachers' materials** and **grades**

## What about parsing part?
[**ktmuscrap**](https://github.com/kerdl/ktmuscrap) is a parsing HTTP REST API server written in 🚀BLAZINGLY FAST HIT VIDEO GAME - RUST🚀

Server runs on localhost, providing simple API for this bot, such as:
- getting **daily** or **weekly** schedule's JSON both **fully** or **for specific group to 🚀SAVE EXTRA MILLISECOND🚀**
- force update with a POST request if user pressed the **Update** button
- subscription to update events using WebSocket, which sends all detailed schedule changes

More in [**ktmuscrap's** README](https://github.com/kerdl/ktmuscrap/blob/master/README.md) 😮😮😮😮

## Improvements
[Issues](https://github.com/kerdl/ktmuslave/issues) is the most **VALUABLE©** and **TRUSTED®** source of planned improvements (since this is my portfolio and I wanna look responsible) on this unpopular bullshit

## All features
- [**Shit temp database**](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/__init__.py#L41-L87) (pi... pikc.. pickle in my ass bro 😳....)
  - [User's navigation states](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/states/tree.py)
  - [User's settings](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/settings.py#L17-L22)
  - [User's Zoom data storage](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/zoom.py#L472-L499)
  - [Other insignificant shit for bot to work](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/__init__.py#L52-L87)
- [**Custom router for handlers that work both for VK and Telegram**](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/router.py)
  - Decorators, so handlers register automatically ([🎍 decorators](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/router.py#L37-L74))
  - Filters, like only activate the handler on specific callback ([🚽 basic filters](https://github.com/kerdl/ktmuslave/blob/master/src/svc/common/filters.py))
  - Router, checks filters and calls the handler that have passed ([⚙️ implementation](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/router.py#L103-L165))
  - Registration handlers (ur a newbie), to set initial settings like your group, if you wish a broadcast and to add Zoom data ([⚙️ handlers](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/init.py))
  - Hub handlers (ur a pro user), to view the schedule, useful links and change settings ([⚙️ handlers](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/hub.py))
  - Zoom data handlers (u add teachers' zoom), to add a teacher, an URL, ID, password and notes for him ([⚙️ handlers](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/zoom.py))
- [**Navigation**](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/navigator.py)
  - Back and Next buttons ([➕ automatic button add](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/keyboard.py#L270-L280), [⚙️ back implementation](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/__init__.py#L83-L86))
  - State tree formatting on register state, so user knows how long it will take ([🖌️ formatter](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/states/formatter.py#L38-L145))
  - Pagination for large data: Zoom storage in this case ([⚙️ implementation](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/pagination.py#L54-L165))
- [**Zoom storage**](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/zoom.py)
  - Ability to add/modify/delete an entry manually ([⛏️ selecting an entry](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/zoom.py#L418-L429), [✏️ entry's field edit](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/zoom.py#L65-L155))
  - Ability to add multiple records from one user's message ([🤓 message parser](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/parse/zoom.py#L223-L234))
  - Warnings about possibly incorrect data format ([✔️ checks](https://github.com/kerdl/ktmuslave/blob/master/src/data/zoom.py#L149-L156), [⚠️ all possible warnings](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/__init__.py#L123-L156))
  - Ability to dump all data to text, which can be loaded in a different chat ([💾 dump button](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/zoom.py#L452), [💥 what happens on press](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/zoom.py#L15-L26))
  - Lots of byautoful text formatting ([🖌️ formatter](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/zoom.py#L244-L255))
- **Schedule**
  - Broadcast on any changes received from WebSocket server ([🔄 event loop](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/api/schedule.py#L310-L365))
  - Format of changes, what day, subject and data inside it exactly have changed ([🖌️ formatter](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/schedule/format.py#L245-L315))
  - Replying to the last schedule message to quickly see schedule's history ([↩️ reply conditions](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/__init__.py#L208-L226))
  - Ability to force invoke global schedule update if someone noticed a change between 10 min auto-update period ([🔄 update button](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/hub.py#L114), [💥 what happens on press](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/hub.py#L20-L59))
  - Lots of byautoful text formatting ([🖌️ formatter](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/schedule/format.py#L208-L238))
- **Other**
  - Notify for bot's admin in case of any exception raise ([⚙️ implementation](https://github.com/kerdl/ktmuslave/blob/e7990a044526435c49471ed8be06871ce0c50384/src/__init__.py#L61-L75))