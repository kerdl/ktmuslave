# Code structure tour
Some directories have a `README.md`
describing the purpose of
included files and folders.


## Initialization
Happens in
[`src.Defs.init_all()`](/src/__init__.py?blame=1#L140).
- Logger initialization
- Reading settings
- Connecting to Redis and setting it up
- Loading interaction handlers


## Interactions
When the user send a message or presses
a button, this interaction is accepted by
[`src.svc.common.router.Router`](/src/svc/common/router.py?blame=1#L146).

Interaction goes through middlewares in
[`src.svc.common.middlewares`](/src/svc/common/middlewares.py).
The interaction is logged, filtered,
user's database entry is loaded into it
and saved after execution.

Next, the according event handler is searched in
[`src.svc.common.bps`](/src/svc/common/bps).


## Schedule update loop
Loop happens in [`src.api.schedule.ScheduleApi.updates()`](/src/api/schedule.py?blame=1#L168).

Notifications sent by **ktmuscrap**
are processed and broadcasted if needed.


## Weekly broadcast
Loop happens in
[`src.Defs.weekcast_loop()`](/src/__init__.py?blame=1&L280).


## Message texts
Texts are located in
[`src.svc.common.messages`](/src/svc/common/messages.py).


## Schedule formatting
Schedules are formatted in
[`src.data.schedule.format.formation()`](/src/data/schedule/format.py?blame=1#L523).

Changes are formatted in
[`src.data.schedule.format.cmp()`](/src/data/schedule/format.py?blame=1#L605).


## Parsing messages with Zoom data
- For groups -
[`src.parse.zoom.Parser.group_parse()`](/src/parse/zoom.py?blame=1#L309)
- For teachers -
[`src.parse.zoom.Parser.teacher_parse()`](/src/parse/zoom.py?blame=1#L330)
