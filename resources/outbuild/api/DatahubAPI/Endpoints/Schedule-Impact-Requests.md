<!-- Source: https://pp-docs.outbuild.com/docs/DatahubAPI/Endpoints/Schedule%20Impact%20Requests -->

# Schedule Impact Requests

The endpoint described in this section retrieves information on Schedule Impact Requests (SIRs) associated with a specific schedule in your organization.

# Schedule Impact Requests

1. [Endpoint 1: GET all schedule impact requests for a specific schedule](#request-scheduleimpactrequestsschedulescheduleid)

## `GET` /scheduleimpactrequests/schedule/{scheduleId}

### Description

*This endpoint retrieves a list of an organization's schedule impact requests for a specific schedule, including fully joined activity, user, source event, and impacted task data.*

A Schedule Impact Request (SIR) is a formal change request created when a task's dates conflict with its parent activity's scheduled dates. Each SIR captures the original and proposed dates, the variance, and the approval workflow state.

> **📄 Pagination**: The endpoint returns **500** schedule impact requests per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/scheduleimpactrequests/schedule/{scheduleId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/scheduleimpactrequests/schedule/100?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/scheduleimpactrequests/schedule/100`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of schedule impact requests for a specific schedule, with nested objects for the activity, users (requester, reviewer, resolver), source events and their responsibles, and impacted tasks and their responsibles.

If no schedule impact requests are available for the specific schedule, the response body will be empty (`[]`).

##### Example response

```json
  {
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "page": 1,
    "hasNextPage": false,
    "schedule_impact_requests": [
      {
        "id": 82378,
        "request_code": "10980-2",
        "state": "pending",
        "reason": "Delay in concrete pour",
        "review_comment": null,
        "variance": -14,
        "schedule_impact": null,
        "compensable_type": "compensable",
        "excusable_type": "excusable",
        "is_critical": false,
        "original_start_date": "2024-08-19T06:00:00.000",
        "new_start_date": "2024-08-19T06:00:00.000",
        "original_end_date": "2024-09-27T14:00:00.000",
        "new_end_date": "2024-09-13T14:00:00.000",
        "requested_at": "2026-03-03T14:33:06.612",
        "submitted_at": "2026-03-03T14:33:06.612",
        "reviewed_at": null,
        "created_at": "2026-03-03T14:33:06.612",
        "updated_at": "2026-03-03T14:33:06.612",
        "schedule_id": 10980,
        "project_id": 3177,
        "organization_id": 23,
        "activity": {
          "id": 11204214,
          "name": "50% CD's"
        },
        "requester": {
          "id": 14167,
          "name": "Gonzalo",
          "lastname": "Fernández",
          "email": "[email protected]"
        },
        "reviewer": {
          "id": 14167,
          "name": "Gonzalo",
          "lastname": "Fernández",
          "email": "[email protected]"
        },
        "resolver": null,
        "source_events": [
          {
            "id": 1146,
            "type": "task",
            "task_id": 3496146,
            "roadblock_id": null,
            "rfv_id": null,
            "company_id": 1358,
            "event_data": {
              "status": "Overdue",
              "event_date": "2024/09/13 14:00",
              "event_name": "Concrete pour",
              "company_name": "Electrical Inc.",
              "company_color": "#f0f113"
            },
            "created_at": "2026-03-03T14:33:06.648",
            "updated_at": "2026-03-03T14:33:06.648",
            "responsibles": [
              {
                "id": 133,
                "responsible_id": 4107,
                "responsible_data": {
                  "name": "Joe",
                  "email": "[email protected]",
                  "image_url": null,
                  "last_name": "Plumb"
                },
                "created_at": "2026-03-03T14:33:06.656"
              }
            ]
          }
        ],
        "impacted_tasks": [
          {
            "id": 13806,
            "task_id": 3984336,
            "task_name": "Concrete pour",
            "start_date": "2024-09-10T06:00:00.000",
            "end_date": "2024-09-13T14:00:00.000",
            "company_id": 1358,
            "company_name": "Concrete Inc.",
            "company_color": "#818181",
            "start_modification_type": null,
            "end_modification_type": "early",
            "created_at": "2026-03-03T14:33:06.670",
            "responsibles": [
              {
                "responsible_id": 34013,
                "name": "Katrina",
                "lastname": "Keyes",
                "email": "[email protected]",
                "image_url": null
              }
            ]
          }
        ]
      }
    ]
  }
}
```

#### Properties overview

As the endpoint **is paginated**, the response additionally includes the following fields:

- **`page`**: Indicates the current page number that was either provided in the request URL or defaulted to 1.
- **`hasNextPage`**: Indicates if there are more pages of data present in the database.
  
  - If `true`, aditional data, corresponding to next page (`page + 1`) exists.
  - If `false`, no more matching data exists, and subsequent pages will return an empty list (`[]`).

You can find information about each data field in the sections below.

**Click to view a detailed explanation of the top-level fields for each schedule impact request**

| Name | Description | Type |
|---|---|---|
| `id` | Unique schedule impact request identifier | Number |
| `request_code` | Human-readable code for the SIR (format: `{scheduleId}-{sequentialNumber}`) | Text |
| `state` | Current state of the request (`pending`, `approved`, or `rejected`) | Text |
| `reason` | Reason provided by the requester for the schedule change | Text |
| `review_comment` | Comment left by the reviewer when approving or rejecting (null if pending) | Text or null |
| `variance` | Calendar day difference between original and new end dates | Number |
| `schedule_impact` | Overall schedule impact in days (null if not calculated) | Number or null |
| `compensable_type` | Delay compensation classification (`compensable`, `notcompensable`, `notdefined`) | Text |
| `excusable_type` | Delay excusability classification (`excusable`, `notexcusable`, `notdefined`) | Text |
| `is_critical` | Whether the affected activity is on the critical path | Boolean |
| `original_start_date` | Original planned start date of the activity before the change | Date |
| `new_start_date` | Proposed new start date for the activity | Date |
| `original_end_date` | Original planned end date of the activity before the change | Date |
| `new_end_date` | Proposed new end date for the activity | Date |
| `requested_at` | Timestamp when the SIR was created | Date |
| `submitted_at` | Timestamp when the SIR was submitted for review | Date |
| `reviewed_at` | Timestamp when the SIR was reviewed (null if pending) | Date or null |
| `created_at` | Timestamp when the record was created | Date |
| `updated_at` | Timestamp when the record was last updated | Date |
| `schedule_id` | Identifier of the associated schedule | Number |
| `project_id` | Identifier of the associated project | Number |
| `organization_id` | Identifier of the associated organization | Number or null |
| `activity` | The affected activity (see nested fields below) | Object |
| `requester` | The user who created the SIR (see nested fields below) | Object |
| `reviewer` | The user assigned to review the SIR (null if not assigned) | Object or null |
| `resolver` | The user who resolved the SIR (null if not resolved) | Object or null |
| `source_events` | List of events that caused the schedule impact (see nested fields below) | Array of Objects |
| `impacted_tasks` | List of tasks affected by the schedule change (see nested fields below) | Array of Objects |

**Click to view a detailed explanation of the activity nested object**

| Name | Description | Type |
|---|---|---|
| `id` | Unique activity identifier | Number |
| `name` | Activity name (snapshot at SIR creation) | Text |

**Click to view a detailed explanation of the requester / reviewer / resolver nested objects**

| Name | Description | Type |
|---|---|---|
| `id` | Unique user identifier | Number |
| `name` | User's first name | Text |
| `lastname` | User's last name | Text |
| `email` | User's email address | Text |

**Click to view a detailed explanation of each source event in the `source_events` array**

Source events represent the root cause that triggered the schedule impact. Each event is polymorphic — only one of `task_id`, `roadblock_id`, `rfv_id`, or `company_id` will be populated depending on the `type`.

| Name | Description | Type |
|---|---|---|
| `id` | Unique source event identifier | Number |
| `type` | Type of source event (`task`, `roadblock`, `rfv`, or `company`) | Text |
| `task_id` | Identifier of the associated task (null if type is not `task`) | Number or null |
| `roadblock_id` | Identifier of the associated roadblock (null if type is not `roadblock`) | Number or null |
| `rfv_id` | Identifier of the associated RFV (null if type is not `rfv`) | Number or null |
| `company_id` | Identifier of the associated company (null if type is not `company`) | Number or null |
| `event_data` | Snapshot of the event details at creation time (JSON object) | Object |
| `created_at` | Timestamp when the source event was created | Date |
| `updated_at` | Timestamp when the source event was last updated | Date |
| `responsibles` | List of users responsible for this source event | Array of Objects |

Each **responsible** in a source event contains:

| Name | Description | Type |
|---|---|---|
| `id` | Unique responsible record identifier | Number |
| `responsible_id` | Identifier of the responsible user | Number |
| `responsible_data` | Snapshot of the responsible user's details (JSON object) | Object |
| `created_at` | Timestamp when the record was created | Date |

**Click to view a detailed explanation of each impacted task in the `impacted_tasks` array**

Impacted tasks are the tasks whose date changes triggered the SIR. Their names and company data are snapshots captured at SIR creation time.

| Name | Description | Type |
|---|---|---|
| `id` | Unique impacted task record identifier | Number |
| `task_id` | Identifier of the task | Number |
| `task_name` | Task name (snapshot at SIR creation) | Text |
| `start_date` | Task start date | Date |
| `end_date` | Task end date | Date |
| `company_id` | Identifier of the company assigned to the task (null if none) | Number or null |
| `company_name` | Company name (snapshot, null if no company assigned) | Text or null |
| `company_color` | Company color hex code (snapshot, null if no company assigned) | Text or null |
| `start_modification_type` | How the start date changed (`early`, `late`, or null) | Text or null |
| `end_modification_type` | How the end date changed (`early`, `late`, or null) | Text or null |
| `created_at` | Timestamp when the record was created | Date |
| `responsibles` | List of users responsible for this task | Array of Objects |

Each **responsible** in an impacted task contains:

| Name | Description | Type |
|---|---|---|
| `responsible_id` | Identifier of the responsible user | Number |
| `name` | User's first name | Text |
| `lastname` | User's last name | Text |
| `email` | User's email address | Text |
| `image_url` | URL to the user's profile image | Text or null |

#### ⚠️Failure

The endpoint will return the following response if the request fails:

```json
  {
    "status" : ERROR_CODE,
    "body": {
      "message": ERROR_MESSAGE
    }
  }
```

Where the error codes and the errores messages are as follows:

| `ERROR_CODE` | `ERROR_MESSAGE` | Explanation |
|---|---|---|
| 400 | Required URL parameters are either missing from the request or are invalid. | The `scheduleId` parameter was not provided in the URL or is not a valid integer. |
| 401 | Unauthorized access: required auth information is missing from the request. | Insufficient authorization data was provided |
| 401 | Unauthorized access: organization id is invalid or is not permitted. | The token does not correspond to a valid organization |
| 401 | Unauthorized access: user role is invalid or is not permitted. | The token does not grant sufficient access permissions |
| 401 | Unauthorized access: user id is invalid or is not permitted. | The token does not correspond to a valid user |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Example request using cURL

Use the following curl example to connect to the production endpoint:

```bash
  curl -X GET "https://datahub.outbuild.com/scheduleimpactrequests/schedule/{scheduleId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```
