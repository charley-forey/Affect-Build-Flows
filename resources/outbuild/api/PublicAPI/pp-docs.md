<!-- Source: https://pp-docs.outbuild.com/docs/PublicAPI/pp-docs -->

# pp-docs

## Activity

**Activity - Getting a range lookahead**

POST - [https://publicapi.outbuild.com/api/activitys/lookahead](https://publicapi.outbuild.com/api/activitys/lookahead)

---

**Permission:** master

Description: `This endpoint will allow you, to get exactly lookahead data used in Outbuild, since an start and end date (lookahead range) and a sector ID.`

**Header**

| **Field** | Type | Description |
|---|---|---|
| Content-Type | String | application/json |
| authorization | string | Basic YOUR_APP_KEY_AUTH |
| www-authenticate | String | Bearer YOUR_API_TOKEN |

**Parameter**

| **Field** | Type | Description |
|---|---|---|
| end **optional** | Object | end of range to request activities |
| start **optional** | Object | start of range to request activities |
| sector **optional** | Object | sector_id to get lookahead |
| ignore_dates **optional** | Object | allows to ignore the date range for the activity request, and get WHOLE sector schedule data |

```json title="Request-Example"
POST /api/activitys/lookahead HTTP/1.1
Host: openapi.outbuild.com
authorization: Basic YOUR_APP_KEY_AUTH
www-authenticate: Bearer YOUR_API_TOKEN
Content-Length: 103

{
    "end": "2022/02/13",
    "ignore_dates": true,
    "sector_id": 1059,
    "start": "2022/02/07"
}
```

**Sucess 200**

| **Field** | Type | Description |
|---|---|---|
| weekcommitments | Array | 's data. |

```json title="Success-Response"
{
    "lookahead": [
        {
            "start_date": "2021/12/23 8:00",
            "end_date": "2022/02/16 18:00",
            "id": 1122324,
            "parent_id": "4",
            "unique_id": "6",
            "description": "",
            "name": "Tarea 5",
            "duration": 40,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 100,
            "constraint": "As soon As Possible",
            "type": "task",
            "correlative_id": 5,
            "has_childs": false,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 43.956043956043956,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 0,
            "reCalculatePonderator": null,
            "freeSlack": 2104,
            "is_critical": false,
            "createdAt": "2021-07-06T16:11:17.685Z",
            "updatedAt": "2022-01-17T15:59:58.905Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": null,
            "subcontractId": null,
            "tasks": [],
            "responsables": []
        }
    ],
    "activities": [
        {
            "start_date": "2021/12/23 8:00",
            "end_date": "2022/02/16 18:00",
            "id": 1122324,
            "parent_id": "4",
            "unique_id": "6",
            "description": "",
            "name": "Tarea 5",
            "duration": 40,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 100,
            "constraint": "As soon As Possible",
            "type": "task",
            "correlative_id": 5,
            "has_childs": false,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 43.956043956043956,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 0,
            "reCalculatePonderator": null,
            "freeSlack": 2104,
            "is_critical": false,
            "createdAt": "2021-07-06T16:11:17.685Z",
            "updatedAt": "2022-01-17T15:59:58.905Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": null,
            "subcontractId": null,
            "tasks": [],
            "responsables": [],
            "activities": [],
            "activityRoute": "años buenos > Tarea 1 > Tarea 3",
            "activityRouteIds": [
                {
                    "correlative_id": 0,
                    "id": 1122319,
                    "unique_id": "1",
                    "name": "años buenos",
                    "start_date": "2020/12/24 8:00",
                    "duration": 563,
                    "end_date": "2023/02/20 18:00",
                    "parent_id": "0",
                    "progress": 43.4,
                    "ponderator": 0
                },
                {
                    "correlative_id": 1,
                    "id": 1122320,
                    "unique_id": "2",
                    "name": "Tarea 1",
                    "start_date": "2020/12/24 8:00",
                    "duration": 563,
                    "end_date": "2023/02/20 18:00",
                    "parent_id": "1",
                    "progress": 43.4,
                    "ponderator": 100
                },
                {
                    "correlative_id": 3,
                    "id": 1122322,
                    "unique_id": "4",
                    "name": "Tarea 3",
                    "start_date": "2021/10/14 8:00",
                    "duration": 90,
                    "end_date": "2022/02/16 18:00",
                    "parent_id": "2",
                    "progress": 98.92,
                    "ponderator": 39.224137931034484
                }
            ]
        }
    ],
    "resource": [
        {
            "id": 36304,
            "name": "Leonel Medina",
            "type": "material",
            "material_label": "Un",
            "total": 0,
            "used": 0,
            "unique_id": 5,
            "createdAt": "2021-06-25T21:23:40.935Z",
            "updatedAt": "2021-06-25T21:23:40.935Z",
            "sectorId": 1059
        },
    ],
    "taktRelations": []
}
```

**Error 4xx**

| **Name** | Type | Description |
|---|---|---|
| 400 | Object | Some parameters may contain invalid values. |

## Company

**Company - Getting company with their sectors from company ID**

GET - [https://publicapi.outbuild.com/api/companys/:id](https://publicapi.outbuild.com/api/companys/:id)

---

Description: `This will allow you once you get your get your API token through the /api/auth endpoint, to get whole company data, and their sectors created in Outbuild`

**Header**

| **Field** | Type | Description |
|---|---|---|
| authorization | string | YOUR_APP_KEY_AUTH |
| www-authenticate | String | Bearer YOUR_API_TOKEN |

```json title="Request-Example"
GET /api/companys/3 HTTP/1.1
Host: openapi.outbuild.com
authorization: Basic YOUR_APP_KEY_AUTH
www-authenticate: Bearer YOUR_API_TOKEN
```

**Success 200**

| **Field** | Type | Description |
|---|---|---|
| company | Object | company's data |

```json title="Success-Response"
{
    "company": {
        "id": 3,
        "name": "name",
        "image": null,
        "contact_email": null,
        "contact_name": null,
        "contact_number": null,
        "country": "AX",
        "size": "a",
        "address": null,
        "geo_victoria_config": null,
        "createdAt": "2020-08-27T00:10:52.088Z",
        "updatedAt": "2022-02-01T18:11:09.726Z",
        "projects": [
            {
                "id": 3,
                "name": "reet",
                "planification_day": 1,
                "timezone": null,
                "country": "CL",
                "currency": "USD",
                "budget": 23,
                "sizetype": "m2",
                "size": 234,
                "image": "https://proplannerv2.s3.us-east-2.amazonaws.com/images/projects/2021-06-11T17-02-12.082Z.png",
                "type": "residential",
                "stage": "started",
                "archivereason": null,
                "pcr_goal": null,
                "pcc_goal": null,
                "task_creter": "duration",
                "activity_creter": "duration",
                "address": null,
                "geo_project_id": null,
                "hoursPerDay": 9,
                "release_constraint": "no-editable",
                "createdAt": "2020-08-27T00:11:01.594Z",
                "updatedAt": "2021-12-29T20:22:12.079Z",
                "companyId": 3,
                "managerId": null,
                "sectors": [
                    {
                        "id": 1463,
                        "name": "name",
                        "description": null,
                        "status": true,
                        "order": 1,
                        "productive": true,
                        "update_ponderators_lookahead": false,
                        "update_ponderators_masterplan": false,
                        "update_duration_for_primavera_for_end_date": false,
                        "hoursPerDay": 9,
                        "hoursPerWeek": 45,
                        "accumulatedDuration": 27,
                        "update_task_from_activity_moved": true,
                        "dateFormat": "MM/DD/YY",
                        "createdAt": "2021-05-17T22:00:05.351Z",
                        "updatedAt": "2021-12-29T20:22:12.436Z",
                        "projectId": 3
                    },
                    {
                        "id": 1695,
                        "name": "name",
                        "description": null,
                        "status": true,
                        "order": 2,
                        "productive": true,
                        "update_ponderators_lookahead": false,
                        "update_ponderators_masterplan": false,
                        "update_duration_for_primavera_for_end_date": false,
                        "hoursPerDay": 9,
                        "hoursPerWeek": 45,
                        "accumulatedDuration": 3348,
                        "update_task_from_activity_moved": true,
                        "dateFormat": "MM/DD/YY",
                        "createdAt": "2021-06-14T23:05:14.013Z",
                        "updatedAt": "2021-12-29T20:22:12.429Z",
                        "projectId": 3
                    },
                    {
                        "id": 1059,
                        "name": "sfdsf",
                        "description": null,
                        "status": true,
                        "order": 0,
                        "productive": true,
                        "update_ponderators_lookahead": false,
                        "update_ponderators_masterplan": false,
                        "update_duration_for_primavera_for_end_date": false,
                        "hoursPerDay": 9,
                        "hoursPerWeek": 45,
                        "accumulatedDuration": 2088,
                        "update_task_from_activity_moved": true,
                        "dateFormat": "MM/DD/YYYY",
                        "createdAt": "2021-03-11T13:03:27.980Z",
                        "updatedAt": "2022-01-17T15:59:55.134Z",
                        "projectId": 3
                    },
                    {
                        "id": 2554,
                        "name": "sector",
                        "description": null,
                        "status": true,
                        "order": 3,
                        "productive": true,
                        "update_ponderators_lookahead": null,
                        "update_ponderators_masterplan": null,
                        "update_duration_for_primavera_for_end_date": false,
                        "hoursPerDay": 9,
                        "hoursPerWeek": 45,
                        "accumulatedDuration": 441,
                        "update_task_from_activity_moved": true,
                        "dateFormat": "MM/DD/YY",
                        "createdAt": "2021-12-29T20:22:12.434Z",
                        "updatedAt": "2021-12-29T20:38:27.550Z",
                        "projectId": 3
                    }
                ]
            },
        ]
    }
}
```

**Error 4xx**

| **Name** | Description |
|---|---|
| 404 | company not found |

## Roadblocks

**Roadblocks - Getting all sector roadblocks from sector ID**

GET - [https://publicapi.outbuild.com/api/constraints/sector/:sector_id](https://publicapi.outbuild.com/api/constraints/sector/:sector_id)

---

**Permission:** master

Description: `This will retrieve whole sector roadblocks`

**Header**

| **Field** | Type | Description |
|---|---|---|
| authorization | string | Basic YOUR_APP_KEY_AUTH |
| www-authenticate | String | Bearer YOUR_API_TOKEN |

```json title="Request-Example"
GET /api/constraints/sector/1059 HTTP/1.1
Host: openapi.outbuild.com
authorization: Basic YOUR_APP_KEY_AUTH
www-authenticate: Bearer YOUR_API_TOKEN
```

**Sucess 200**

| **Field** | Type | Description |
|---|---|---|
| constraint | Object | constraint's data |

```json title="Success-Response"
{
    "constraints": [
        {
            "commitmentDate": "2021/11/24 15:57",
            "deadline": "2021/11/24 15:57",
            "id": 9930,
            "name": "name",
            "priority": "normal",
            "status": "draft",
            "constraintTypeId": 1181,
            "userId": 514,
            "release_date": null,
            "release_user": null,
            "report_user": null,
            "identify_user": 3,
            "description": null,
            "link": "https://new.proplanner.cl/lookahead/constraints/3/1059",
            "createdAt": "2021-11-24T15:57:13.496Z",
            "updatedAt": "2022-01-27T14:42:27.312Z",
            "sectorId": 1059,
            "releaseuser": null,
            "reportuser": null,
            "schedules": [],
            "tasks": [],
            "typeName": "typename",
            "typeArea": "design",
            "userName": "username"
        },
        {
            "commitmentDate": "2021/07/21 22:01",
            "deadline": "2021/07/23 0:00",
            "id": 7227,
            "name": "name",
            "priority": "normal",
            "status": "expired",
            "constraintTypeId": 1181,
            "userId": 3,
            "release_date": null,
            "release_user": null,
            "report_user": null,
            "identify_user": 3,
            "description": null,
            "link": null,
            "createdAt": "2021-07-21T22:02:00.573Z",
            "updatedAt": "2022-02-01T05:35:00.011Z",
            "sectorId": 1059,
            "releaseuser": null,
            "reportuser": null,
            "schedules": [],
            "tasks": [],
            "typeName": "typename",
            "typeArea": "design",
            "userName": "username"
        },
        {
            "commitmentDate": "2021/11/24 16:05",
            "deadline": "2021/11/24 16:05",
            "id": 9931,
            "name": "name",
            "priority": "normal",
            "status": "expired",
            "constraintTypeId": 1181,
            "userId": 514,
            "release_date": null,
            "release_user": null,
            "report_user": null,
            "identify_user": 3,
            "description": null,
            "link": "https://new.proplanner.cl/lookahead/constraints/3/1059",
            "createdAt": "2021-11-24T16:05:32.552Z",
            "updatedAt": "2022-02-01T05:35:00.011Z",
            "sectorId": 1059,
            "releaseuser": null,
            "reportuser": null,
            "schedules": [],
            "tasks": [],
            "typeName": "typename",
            "typeArea": "design",
            "userName": "username"
        },
        {
            "commitmentDate": "2021/10/02 21:45",
            "deadline": "2021/10/02 21:45",
            "id": 8938,
            "name": "sdfds",
            "priority": "normal",
            "status": "expired",
            "constraintTypeId": 1181,
            "userId": 3,
            "release_date": null,
            "release_user": null,
            "report_user": 514,
            "identify_user": 3,
            "description": null,
            "link": null,
            "createdAt": "2021-10-02T21:45:30.188Z",
            "updatedAt": "2022-02-01T05:35:00.011Z",
            "sectorId": 1059,
            "releaseuser": null,
            "reportuser": {
                "id": 514,
                "email": "usuario@dominio",
                "password": "passwd",
                "role": "role",
                "name": "name",
                "lastname": "lastname",
                "is_active": true,
                "activation_token": "activation token",
                "country": null,
                "position": null,
                "image": null,
                "dni": null,
                "createdAt": "2020-10-19T20:55:24.887Z",
                "updatedAt": "2021-12-20T16:40:57.642Z",
                "companyId": 3
            },
            "schedules": [],
            "tasks": [],
            "typeName": "nvbvvhgvgh",
            "typeArea": "design",
            "userName": "dfdfgfdg dfgdf"
        },
    ]
}
```

**Error 4xx**

| **Name** | Description |
|---|---|
| 404 | constraint not found |

## Sector

**Sector - Getting activities using sector ID**

GET - [https://publicapi.outbuild.com/api/activitys/sector/:sector_id](https://publicapi.outbuild.com/api/activitys/sector/:sector_id)

---

**Permission:** master

Description: `Once we get the company data, we can choose one sector ID to get their activities. using YOUR_API_TOKEN through auth endpoint, and also YOUR_APP_KEY_AUTH given.`

**Header**

| **Field** | Type | Description |
|---|---|---|
| authorization | string | Basic YOUR_APP_KEY_AUTH |
| www-authenticate | String | Bearer YOUR_API_TOKEN |

```json title="Request-Example"
GET /api/activitys/sector/1059 HTTP/1.1
Host: openapi.outbuild.com
authorization: Basic YOUR_APP_KEY_AUTH
www-authenticate: Bearer YOUR_API_TOKEN
```

**Sucess 200**

| **Field** | Description |
|---|---|
| Array **optional** | sector activities data |

```json title="Success-Response"
{
    "activity": [
        {
            "start_date": "2021/10/14 8:00",
            "end_date": "2021/10/14 18:00",
            "id": 1208378,
            "parent_id": "4",
            "unique_id": "1627664605994",
            "description": "",
            "name": "New Activity",
            "duration": 1,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 1.83418928833456,
            "constraint": "As soon As Possible",
            "type": "task",
            "correlative_id": 6,
            "has_childs": false,
            "isOnLookahead": true,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 1.0989010989011,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 0,
            "reCalculatePonderator": null,
            "freeSlack": 2816,
            "is_critical": false,
            "createdAt": "2021-07-30T17:04:19.171Z",
            "updatedAt": "2022-01-17T16:00:01.438Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": 27655,
            "subcontractId": null,
            "activitymodifications": [
                {
                    "startOriginal": "2021/10/14 8:00",
                    "startNew": "2021/09/21 8:00",
                    "endOriginal": "2021/10/14 18:00",
                    "endNew": "2022/01/06 16:00",
                    "id": 6246,
                    "type": "both",
                    "state": "waiting",
                    "description": "dsfs",
                    "createdAt": "2021-09-22T16:11:05.189Z",
                    "updatedAt": "2021-09-22T16:11:05.189Z",
                    "activityId": 1208378,
                    "userRequestId": 3,
                    "userApprovedId": null,
                    "userId": null,
                    "userRequest": {
                        "id": 3,
                        "email": "usuario@dominio",
                        "password": "passwd",
                        "role": "role",
                        "name": "name",
                        "lastname": null,
                        "is_active": true,
                        "activation_token": "activation_token",
                        "country": null,
                        "position": "director",
                        "image": "https://proplannerv2.s3.us-east-2.amazonaws.com/images/users/2021-06-30T18-42-50.293Z.jpeg",
                        "dni": null,
                        "createdAt": "2020-08-27T00:09:48.429Z",
                        "updatedAt": "2021-12-20T16:40:58.853Z",
                        "companyId": 3
                    },
                    "activity": {
                        "start_date": "2021/10/14 8:00",
                        "end_date": "2021/10/14 18:00",
                        "id": 1208378,
                        "parent_id": "4",
                        "unique_id": "1627664605994",
                        "description": "",
                        "name": "New Activity",
                        "duration": 1,
                        "cost": 0,
                        "used_cost": 0,
                        "real_cost": 0,
                        "progress": 1.83418928833456,
                        "constraint": "As soon As Possible",
                        "type": "task",
                        "correlative_id": 6,
                        "has_childs": false,
                        "isOnLookahead": true,
                        "hhWorkTime": 0,
                        "real_work": 0,
                        "ponderator": 1.0989010989011,
                        "hasCustomPonderator": false,
                        "sumOfDurationRecursively": 0,
                        "reCalculatePonderator": null,
                        "freeSlack": 2816,
                        "is_critical": false,
                        "createdAt": "2021-07-30T17:04:19.171Z",
                        "updatedAt": "2022-01-17T16:00:01.438Z",
                        "ganttId": 2083,
                        "sectorId": 1059,
                        "calendarId": 27655,
                        "subcontractId": null
                    }
                }
            ],
            "responsables": [],
            "subcontract": null,
            "tags": []
        },
        {
            "constraint_date": "2021/07/07 8:00",
            "start_date": "2020/12/24 8:00",
            "end_date": "2021/07/30 18:00",
            "id": 1130136,
            "parent_id": "1625670584876",
            "unique_id": "1625670584877",
            "description": "",
            "name": "ya tu sabes",
            "duration": 157,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 96.93,
            "constraint": "Start No Earlier Than",
            "type": "project",
            "correlative_id": 15,
            "has_childs": true,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 100,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 11,
            "reCalculatePonderator": null,
            "freeSlack": null,
            "is_critical": false,
            "createdAt": "2021-07-07T15:20:21.136Z",
            "updatedAt": "2022-01-17T16:00:02.000Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": 27655,
            "subcontractId": null,
            "activitymodifications": [],
            "responsables": [],
            "subcontract": null,
            "tags": []
        },
        {
            "start_date": "2020/12/24 8:00",
            "end_date": "2021/07/30 18:00",
            "id": 1130132,
            "parent_id": "1625670584872",
            "unique_id": "1625670584873",
            "description": "",
            "name": "New Activity",
            "duration": 157,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 96.93,
            "constraint": "As soon As Possible",
            "type": "project",
            "correlative_id": 11,
            "has_childs": true,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 100,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 11,
            "reCalculatePonderator": null,
            "freeSlack": null,
            "is_critical": false,
            "createdAt": "2021-07-07T15:20:21.108Z",
            "updatedAt": "2022-01-17T16:00:02.556Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": 27655,
            "subcontractId": null,
            "activitymodifications": [],
            "responsables": [],
            "subcontract": null,
            "tags": []
        },
        {
            "start_date": "2020/12/24 8:00",
            "end_date": "2020/12/24 18:00",
            "id": 1130146,
            "parent_id": "1625670584995",
            "unique_id": "1625670584997",
            "description": "",
            "name": "New Activity",
            "duration": 1,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 100,
            "constraint": "As soon As Possible",
            "type": "task",
            "correlative_id": 25,
            "has_childs": false,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 9.09090909090909,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 0,
            "reCalculatePonderator": null,
            "freeSlack": 4545,
            "is_critical": false,
            "createdAt": "2021-07-07T15:26:39.716Z",
            "updatedAt": "2022-01-17T16:00:03.116Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": 27655,
            "subcontractId": null,
            "activitymodifications": [],
            "responsables": [],
            "subcontract": null,
            "tags": []
        },
        {
            "start_date": "2020/12/24 8:00",
            "end_date": "2021/07/30 18:00",
            "id": 1130138,
            "parent_id": "1625670584989",
            "unique_id": "1625670584990",
            "description": "",
            "name": "New Activity",
            "duration": 157,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 96.93,
            "constraint": "As soon As Possible",
            "type": "project",
            "correlative_id": 17,
            "has_childs": true,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 100,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 11,
            "reCalculatePonderator": null,
            "freeSlack": null,
            "is_critical": false,
            "createdAt": "2021-07-07T15:26:39.672Z",
            "updatedAt": "2022-01-17T16:00:03.680Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": 27655,
            "subcontractId": null,
            "activitymodifications": [],
            "responsables": [],
            "subcontract": null,
            "tags": []
        },
        {
            "constraint_date": "2021/09/06 8:00",
            "start_date": "2021/09/06 8:00",
            "end_date": "2021/12/24 18:00",
            "id": 1122321,
            "parent_id": "2",
            "unique_id": "3",
            "description": "",
            "name": "Tarea 2",
            "duration": 80,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 0,
            "constraint": "Start No Earlier Than",
            "type": "task",
            "correlative_id": 2,
            "has_childs": false,
            "isOnLookahead": true,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 34.4827586206897,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 0,
            "reCalculatePonderator": null,
            "freeSlack": -468,
            "is_critical": false,
            "createdAt": "2021-07-06T16:11:17.684Z",
            "updatedAt": "2022-01-17T15:59:57.205Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": null,
            "subcontractId": null,
            "activitymodifications": [],
            "responsables": [],
            "subcontract": null,
            "tags": []
        },
        {
            "start_date": "2020/12/24 8:00",
            "end_date": "2021/07/30 18:00",
            "id": 1130143,
            "parent_id": "1625670584994",
            "unique_id": "1625670584995",
            "description": "",
            "name": "New Activity",
            "duration": 157,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 96.93,
            "constraint": "As soon As Possible",
            "type": "project",
            "correlative_id": 22,
            "has_childs": true,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 100,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 11,
            "reCalculatePonderator": null,
            "freeSlack": null,
            "is_critical": false,
            "createdAt": "2021-07-07T15:26:39.700Z",
            "updatedAt": "2022-01-17T16:00:04.242Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": 27655,
            "subcontractId": null,
            "activitymodifications": [],
            "responsables": [],
            "subcontract": null,
            "tags": []
        },
        {
            "start_date": "2021/07/19 8:00",
            "end_date": "2021/07/30 18:00",
            "id": 1130144,
            "parent_id": "1625670584995",
            "unique_id": "1625670584996",
            "description": "",
            "name": "New Activity",
            "duration": 10,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 96.62,
            "constraint": "As soon As Possible",
            "type": "project",
            "correlative_id": 23,
            "has_childs": true,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 90.9090909090909,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 10,
            "reCalculatePonderator": null,
            "freeSlack": null,
            "is_critical": false,
            "createdAt": "2021-07-07T15:26:39.705Z",
            "updatedAt": "2022-01-17T16:00:04.799Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": 27655,
            "subcontractId": null,
            "activitymodifications": [],
            "responsables": [],
            "subcontract": null,
            "tags": []
        },
        {
            "start_date": "2020/12/24 8:00",
            "end_date": "2021/07/30 18:00",
            "id": 1130134,
            "parent_id": "1625670584874",
            "unique_id": "1625670584875",
            "description": "",
            "name": "New Activity",
            "duration": 157,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 96.93,
            "constraint": "As soon As Possible",
            "type": "project",
            "correlative_id": 13,
            "has_childs": true,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 100,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 11,
            "reCalculatePonderator": null,
            "freeSlack": null,
            "is_critical": false,
            "createdAt": "2021-07-07T15:20:21.122Z",
            "updatedAt": "2022-01-17T16:00:05.360Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": 27655,
            "subcontractId": null,
            "activitymodifications": [],
            "responsables": [],
            "subcontract": null,
            "tags": []
        },
        {
            "start_date": "2020/12/24 8:00",
            "end_date": "2021/07/30 18:00",
            "id": 1130131,
            "parent_id": "14",
            "unique_id": "1625670584872",
            "description": "",
            "name": "New Activity",
            "duration": 157,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 96.93,
            "constraint": "As soon As Possible",
            "type": "project",
            "correlative_id": 10,
            "has_childs": true,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 100,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 11,
            "reCalculatePonderator": null,
            "freeSlack": null,
            "is_critical": false,
            "createdAt": "2021-07-07T15:20:21.098Z",
            "updatedAt": "2022-01-17T16:00:05.917Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": 27655,
            "subcontractId": null,
            "activitymodifications": [],
            "responsables": [],
            "subcontract": null,
            "tags": []
        },
        {
            "start_date": "2021/10/14 8:00",
            "end_date": "2021/12/22 18:00",
            "id": 1122323,
            "parent_id": "4",
            "unique_id": "5",
            "description": "",
            "name": "Tarea 4",
            "duration": 50,
            "cost": 0,
            "used_cost": 0,
            "real_cost": 0,
            "progress": 100,
            "constraint": "As soon As Possible",
            "type": "task",
            "correlative_id": 4,
            "has_childs": false,
            "isOnLookahead": false,
            "hhWorkTime": 0,
            "real_work": 0,
            "ponderator": 54.9450549450549,
            "hasCustomPonderator": false,
            "sumOfDurationRecursively": 0,
            "reCalculatePonderator": null,
            "freeSlack": 0,
            "is_critical": false,
            "createdAt": "2021-07-06T16:11:17.684Z",
            "updatedAt": "2022-01-17T15:59:58.338Z",
            "ganttId": 2083,
            "sectorId": 1059,
            "calendarId": null,
            "subcontractId": null,
            "activitymodifications": [],
            "responsables": [
                {
                    "id": 3,
                    "email": "usuario@dominio",
                    "password": "password",
                    "role": "role",
                    "name": "name",
                    "lastname": null,
                    "is_active": true,
                    "activation_token": "activation_token",
                    "country": null,
                    "position": "director",
                    "image": "https://proplannerv2.s3.us-east-2.amazonaws.com/images/users/2021-06-30T18-42-50.293Z.jpeg",
                    "dni": null,
                    "createdAt": "2020-08-27T00:09:48.429Z",
                    "updatedAt": "2021-12-20T16:40:58.853Z",
                    "companyId": 3,
                    "useractivity": {
                        "userId": 3,
                        "activityId": 1122323,
                        "createdAt": "2022-01-17T15:59:58.617Z",
                        "updatedAt": "2022-01-17T15:59:58.617Z"
                    }
                }
            ],
            "subcontract": null,
            "tags": []
        },
    ],
    "baselines": []
}
```

**Error 4xx**

| **Name** | Description |
|---|---|
| 404 | sector not found |

## Weekly commitment

**Weekly commitment - Getting all week commitments from sector ID**

POST - [https://publicapi.outbuild.com/api/weekcommitments/searchbysector](https://publicapi.outbuild.com/api/weekcommitments/searchbysector)

---

**Permission:** master

Description: ``

**Header**

| **Field** | Type | Description |
|---|---|---|
| authorization | string | Basic YOUR_APP_KEY_AUTH |
| www-authenticate | String | Bearer YOUR_API_TOKEN |

**Parameter**

| **Field** | Type | Description |
|---|---|---|
| sector **optional** | Object | sector_id |

```json title="Request-Example"
POST /api/weekcommitments/searchbysector HTTP/1.1
Host: openapi.outbuild.com
authorization: Basic YOUR_APP_KEY_AUTH
www-authenticate: Bearer YOUR_API_TOKEN
Content-Length: 26

{
    "sector_id" : 1059
}
```

**Sucess 200**

| **Field** | Type | Description |
|---|---|---|
| weekcommitments | Array | 's data. |

```json title="Success-Response"
{
    "weekcommitments": [
        {
            "start_date": "2022/01/03 3:00",
            "end_date": "2022/01/09 3:00",
            "id": 7533,
            "commitment_tasks": 1,
            "week": 2,
            "year": 2022,
            "realized_tasks": 0,
            "closed": true,
            "createdAt": "2022-01-04T13:29:36.336Z",
            "updatedAt": "2022-01-10T03:39:21.783Z",
            "sectorId": 1059,
            "taskcommitments": [
                {
                    "start_date": "2021/12/20 8:00",
                    "end_date": "2022/01/11 18:00",
                    "id": 128997,
                    "commitment_percentaje": 88.24,
                    "realized_percentaje": 0,
                    "current_progress_task": 0,
                    "current_commitment_partial": 0,
                    "is_last_level": true,
                    "duration": 17,
                    "total_quantity": null,
                    "plan_endowment": null,
                    "name": "New task",
                    "nameSucontract": null,
                    "createdAt": "2022-01-04T13:29:36.669Z",
                    "updatedAt": "2022-01-10T03:39:21.783Z",
                    "taskId": 552417,
                    "userId": 3,
                    "weekcommitmentId": 7533,
                    "materialId": null,
                    "subcontractId": null
                }
            ]
        },
    ]
}
```

**Error 4xx**

| **Name** | Type | Description |
|---|---|---|
| 400 | Object | Some parameters may contain invalid values |
