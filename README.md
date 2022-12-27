[🇷🇺 Russian](/README-RU.md)

Running on production:
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

### What about parsing part?
[**ktmuscrap**](https://github.com/kerdl/ktmuscrap) is a parsing HTTP REST API server written in 🚀BLAZINGLY FAST HIT VIDEO GAME - RUST🚀

Server runs on localhost, providing simple API for this bot, such as:
- getting **daily** or **weekly** schedule's JSON both **fully** or **for specific group to 🚀SAVE EXTRA MILLISECOND🚀**
- force update with a POST request if user pressed the **Update** button
- subscription to update events using WebSocket, which sends all detailed schedule changes

More in [**ktmuscrap's** README](https://github.com/kerdl/ktmuscrap/blob/master/README.md) 😮😮😮😮

### Improvements
[Issues](https://github.com/kerdl/ktmuslave/issues) is a most **VALUABLE©** and **TRUSTED®** source of planned improvements (since this is my portfolio and I wanna look responsible) on this unpopular bullshit

### All features
- **Shit temp database** (pi... pikc.. pickle in my ass bro 😳....)
  - User's navigation state
  - User's settings
  - User's Zoom data storage
  - Other unsignificant shit for bot to work
- **Custom handlers that work both for VK and Telegram**
  - Decorators (so handlers register automatically)
  - Filters (like to activate the handler on specific callback)
  - Router (checks filters and calls the handler that have passed)
  - Registration handlers (ur a newbie), to set initial settings like your group, if you wish a broadcast and to add Zoom data
  - Hub handlers (ur a pro user), to view the schedule, useful links and change settings
  - Zoom data handlers (u add teachers' zoom), to add a teacher, an URL, ID, password and notes for him
- **Navigation**
  - Back and Next buttons
  - State tree formatting on register state (so user knows how long it will take)
  - Pagination for large data (Zoom storage in this case)
- **Zoom storage**
  - Ability to add/modify/delete an entry manually
  - Ability to add multiple records from one user's message
  - Warnings about possibly incorrect data format
  - Ability to dump all data to text, which can be loaded in a different chat
  - Lots of byautoful text formatting
- **Schedule**
  - Broadcast on any changes recieved from WebSocket server
  - Format of changes, what day, subject and data inside it exactly have changed
  - Replying to the last schedule message to quickly see schedule's history
  - Ability to force invoke global schedule update if someone noticed a change between 10 min auto-update period
  - Lots of byautoful text formatting
