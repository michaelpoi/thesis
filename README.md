# Setup

## Installing MetaDrive

```shell
cd src/api/
git clone https://github.com/metadriverse/metadrive.git --single-branch
```

## Starting Compose

```shell
cd ..
sudo docker compose up --build -d
```


# Usage

If setup was successful, app can be accessed on port `80`.

## Login

You will be automatically redirected to the login page.

Pre-created admin credentials are:

`username`: `admin`

`password`: `admin`

Pre-created user credentials are:

`username`: `user1`

`password`: `user1`

## Admin Page

If you are logged in as admin, you can acess admin page:

http://127.0.0.1/admin

This page provides interfaces for:

1. Scenario Creation - admins can set up driving scenarios with defined config:
    - Scenario Type (Offline or Real-Time)
    - [Map](#map-creation)
    - Number of steps (scenario horizon)
    - Vehicles config:
        - Initial position (x, y)
        - Initial velocity (m/s)
        - Assigned user id (nullable for AV)

2. User Management

3. Scenario Execution - admins can also act as normal users add connect to scenarios (used vehicle ID should be entered)

4. Scenario data Extraction - if scenario is finished admins can download [Execution Logs](#execution-logs).

## Map Creation

Admins can create custom maps under:

http://127.0.0.1/maps

Map is created from a sequence of blocks and can be updated by adding or removing blocks.

## User workflow

Non-admin users interact with a platform from:

http://127.0.0.1/

There users can see only scenarios they are assigned to, and connect to them.

## Execution Logs

For both scenario types execution logs look like the following:

```json
    [
  {
    "step": 0,
    "move": "KEEP_ALIVE", // user`s step (UP, DOWN, LEFT, RIGHT or KEEP_ALIVE for no step) N/A for offline scenarios
    "positions": {
      "agent0": {
        "position": [   // Agent positions
          25.000457763671875,
          4.5316861374544715e-11
        ],
        "velocity": [ // Agent velocity vector
          0.026030950248241425,
          3.790385338930946e-09
        ],
        "heading": 0.0, // Agent heading in radians
        "goal": {   // Agent goal area
          "point": [
            272.0442199707031,
            0.0
          ],
          "region": {
            "center": [
              272.0442199707031,
              0.0
            ],
            "length": 7.5,
            "width": 10.5
          }
        },
        "is_human": true 
      },
      "f1920fc4-4212-4444-bd9e-2aafcbcf5ba4": {
        "position": [ // AV position
          50.00709533691406,
          2.4596333303428253e-10
        ],
        "velocity": [ // AV velocity
          0.29549115896224976,
          2.520716613219065e-08
        ],
        "heading": 0.0,
        "is_human": false
      }
    },
    "termination": {    // Termination statuses from MetaDrive
      "agent0": false,
      "__all__": false
    },
    "truncation": {     // Truncation statuses from MetaDrive
      "agent0": false,
      "__all__": false
    },
    "info": {   // Agent`s info from MetaDrive
      "agent0": {
        "overtake_vehicle_num": 0,
        "velocity": 0.026030950248241702,
        "steering": 0.0,
        "acceleration": 0.0,
        "step_energy": 1.489126761782398e-05,
        "episode_energy": 1.4896769159653472e-05,
        "policy": "EnvInputPolicy",
        "navigation_command": "forward",
        "navigation_forward": true,
        "navigation_left": false,
        "navigation_right": false,
        "action": [
          0,
          0
        ],
        "raw_action": [
          0,
          0
        ],
        "crash_vehicle": false,
        "crash_object": false,
        "crash_building": false,
        "crash_human": false,
        "crash_sidewalk": false,
        "out_of_road": false,
        "arrive_dest": false,
        "max_step": false,
        "env_seed": 0,
        "crash": false,
        "step_reward": 0.0005749029479920877,
        "route_completion": 0.05724399403027834,
        "cost": 0,
        "episode_reward": 0.0005749029479920877,
        "episode_length": 1
      }
    }
  },
  ...]
```

## Swagger

To see available endpoints and test them you can use Swagger UI.

http://127.0.0.1/api/docs

Some endpoints require authentication first.


