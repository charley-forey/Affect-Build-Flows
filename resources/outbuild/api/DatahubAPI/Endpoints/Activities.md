<!-- Source: https://pp-docs.outbuild.com/docs/DatahubAPI/Endpoints/Activities -->

# Activities

The endpoints described in this section retrieve information on activities associated with active schedules in your organization.

# Activities

1. [Endpoint 1: GET all activities](#request-activities)
2. [Endpoint 2: GET all activities for a specific project](#request-activitiesprojectprojectid)
3. [Endpoint 3: GET all activities for a specific project and schedule](#request-activitiesprojectprojectidschedulescheduleid)
4. [Endpoint 4: GET historical activity progress for a schedule](#request-activitiesschedulescheduleidhistorical-progress)

## `GET` /activities

### Description

*This endpoint retrieves a list of an organization's activities.*

> **📄 Pagination**: The endpoint returns **500** activities per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/activities?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/activities?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/activities`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of activities for a specific organization. If no activities are available, the response body will be empty (`[]`).

##### Example response

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "page":1,
    "hasNextPage": true,
    "activities": [
      {
        "id": 14971,
        "parent_id": 43,
        "unique_id": 6524,
        "description": null,
        "name": "Plumbing - Water Lines & Tubs",
        "duration": 5,
        "cost_budgeted": 0,
        "progress": 100,
        "constraint_date": "2016-01-06 08:00:00.000",
        "start_date": "2016-01-06 08:00:00.000",
        "end_date": "2016-04-20 17:00:00.000",
        "constraint_type": "As soon As Possible",
        "activiy_type" : "task",
        "correlative_id": 3066,
        "has_child_activities": false,
        "labor_hours_earned": 0,
        "weight": 4.80656,
        "created_at": "2016-03-05 19:23:33.947Z",
        "updated_at": "2023-01-06 15:10:23.890Z",
        "gantt_id": 4321,
        "schedule_id": 98,
        "calendar_id": 3,
        "cost_actual": 0,
        "cost_earned": 0,
        "labor_hours_budgeted": 0,
        "sum_of_duration_recursively": 0,
        "company_id": 23,
        "free_float": 0,
        "is_critical": false,
        "is_new_ativity": false,
        "unique_correlative_id": 144,
        "organization_id": 12,
        "baseline_start_date": "2016-01-06T08:00:00.000",
        "baseline_end_date": "2016-04-20T17:00:00.000",
        "baseline_duration": 5
      }
      ... // more objects with the same structure
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

**Click to view a detailed explanation of the fields for each activity**

| Name | Description | Type |
|---|---|---|
| `id` | Unique activity identifier | Number |
| `parent_id` | Identifier of the parent activity, if applicable | Number |
| `unique_id` | Unique identifier of the activity within the schedule | Number |
| `description` | Description of the activity | Text |
| `name` | Name of the activity | Text |
| `duration` | Duration of the activity in days | Number |
| `cost_budgeted` | Budgeted cost assigned to the activity | Number |
| `progress` | Current progress of the activity expressed as a percentage (0 to 100) | Number |
| `constraint_date` | Date of the constraint applied to the activity | Date |
| `start_date` | Planned start date of the activity | Date |
| `end_date` | Planned end date of the activity | Date |
| `constraint_type` | Type of constraint applied (e.g., ASAP, ALAP, SNET, FNET, SNLT, FNLT, MSO, or MFO) | Text |
| `activiy_type` | Type of activity. E.g., milestone, task, or project (when it is a parent activity). | Text |
| `correlative_id` | Correlative identifier of the activity. Indicates the order of the activity in a schedule. | Number |
| `has_child_activities` | Indicates whether the activity has child activities | Boolean |
| `labor_hours_earned` | Accumulated labor hours based on the progress made to date | Number |
| `weight` | Weight of the activity in relation to its parent activity | Number |
| `created_at` | Timestamp indicating when the activity was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the activity was last updated | Date in UTC (Zulu Zone) |
| `gantt_id` | Identifier of the associated Gantt schedule | Number |
| `schedule_id` | Identifier of the schedule to which the activity belongs to | Number |
| `calendar_id` | Identifier of the calendar associated with the activity | Number |
| `cost_actual` | Actual cost incurred to date for the activity | Number |
| `cost_earned` | Earned cost value of the activity based on current progress | Number |
| `labor_hours_budgeted` | Budgeted labor hours to complete the activity | Number |
| `sum_of_duration_recursively` | Sum of the duration of all related activities (including child activities). | Number |
| `company_id` | Identifier of the company responsible for the activity | Number |
| `free_float` | Amount of days an activity can be delayed without affecting the start of subsequent activities | Number |
| `is_critical` | Indicates whether the activity is critical within the project path or not | Boolean |
| `is_new_ativity` | Indicates whether the activity was recently added or not | Boolean |
| `unique_correlative_id` | Unique and correlative identifier within the activity. Value displayed in the 'UID' field | Number |
| `organization_id` | Identifier of the organization to which the project belongs to | Number |
| `baseline_start_date` | Baseline start date of the activity from the active baseline version. Null if no baseline exists | Date (nullable) |
| `baseline_end_date` | Baseline end date of the activity from the active baseline version. Null if no baseline exists | Date (nullable) |
| `baseline_duration` | Baseline duration of the activity in days from the active baseline version. Null if no baseline exists | Number (nullable) |

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
| 401 | Unauthorized access: required auth information is missing from the request. | Insufficient authorization data was provided |
| 401 | Unauthorized access: organization id is invalid or is not permitted. | The token does not correspond to a valid organization |
| 401 | Unauthorized access: user role is invalid or is not permitted. | The token does not grant sufficient access permissions |
| 401 | Unauthorized access: user id is invalid or is not permitted. | The token does not correspond to a valid user |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Example request using cURL

Use the following curl example to connect to the production endpoint:

```bash
  curl -X GET "https://datahub.outbuild.com/activities?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /activities/project/{projectId}

### Description

*This endpoint retrieves a list of an organization's activities for a specific project.*

> **📄 Pagination**: The endpoint returns **500** activities per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/activities/project/{projectId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/activities/project/13?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/activities/project/13`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of activities for a specific organization and project. If no activities are available for the specific project or it doesn't exist, the response body will be empty (`[]`).

##### Example response

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "page":1,
    "hasNextPage": true,
    "activities": [
      {
        "id": 14971,
        "parent_id": 43,
        "unique_id": 6524,
        "description": null,
        "name": "Plumbing - Water Lines & Tubs",
        "duration": 5,
        "cost_budgeted": 0,
        "progress": 100,
        "constraint_date": "2016-01-06 08:00:00.000",
        "start_date": "2016-01-06 08:00:00.000",
        "end_date": "2016-04-20 17:00:00.000",
        "constraint_type": "As soon As Possible",
        "activiy_type" : "task",
        "correlative_id": 3066,
        "has_child_activities": false,
        "labor_hours_earned": 0,
        "weight": 4.80656,
        "created_at": "2016-03-05 19:23:33.947Z",
        "updated_at": "2023-01-06 15:10:23.890Z",
        "gantt_id": 4321,
        "schedule_id": 98,
        "calendar_id": 3,
        "cost_actual": 0,
        "cost_earned": 0,
        "labor_hours_budgeted": 0,
        "sum_of_duration_recursively": 0,
        "company_id": 23,
        "free_float": 0,
        "is_critical": false,
        "is_new_ativity": false,
        "unique_correlative_id": 144,
        "organization_id": 12,
        "baseline_start_date": "2016-01-06T08:00:00.000",
        "baseline_end_date": "2016-04-20T17:00:00.000",
        "baseline_duration": 5
      }
      ... // more objects with the same structure
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

**Click to view a detailed explanation of the fields for each activity**

| Name | Description | Type |
|---|---|---|
| `id` | Unique activity identifier | Number |
| `parent_id` | Identifier of the parent activity, if applicable | Number |
| `unique_id` | Unique identifier of the activity within the schedule | Number |
| `description` | Description of the activity | Text |
| `name` | Name of the activity | Text |
| `duration` | Duration of the activity in days | Number |
| `cost_budgeted` | Budgeted cost assigned to the activity | Number |
| `progress` | Current progress of the activity expressed as a percentage (0 to 100) | Number |
| `constraint_date` | Date of the constraint applied to the activity | Date |
| `start_date` | Planned start date of the activity | Date |
| `end_date` | Planned end date of the activity | Date |
| `constraint_type` | Type of constraint applied (e.g., ASAP, ALAP, SNET, FNET, SNLT, FNLT, MSO, or MFO) | Text |
| `activiy_type` | Type of activity. E.g., milestone, task, or project (when it is a parent activity). | Text |
| `correlative_id` | Correlative identifier of the activity. Indicates the order of the activity in a schedule. | Number |
| `has_child_activities` | Indicates whether the activity has child activities | Boolean |
| `labor_hours_earned` | Accumulated labor hours based on the progress made to date | Number |
| `weight` | Weight of the activity in relation to its parent activity | Number |
| `created_at` | Timestamp indicating when the activity was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the project was last updated | Date in UTC (Zulu Zone) |
| `gantt_id` | Identifier of the associated Gantt schedule | Number |
| `schedule_id` | Identifier of the schedule to which the activity belongs to | Number |
| `calendar_id` | Identifier of the calendar associated with the activity | Number |
| `cost_actual` | Actual cost incurred to date for the activity | Number |
| `cost_earned` | Earned cost value of the activity based on current progress | Number |
| `labor_hours_budgeted` | Budgeted labor hours to complete the activity | Number |
| `sum_of_duration_recursively` | Sum of the duration of all related activities (including child activities). | Number |
| `company_id` | Identifier of the company responsible for the activity | Number |
| `free_float` | Amount of days an activity can be delayed without affecting the start of subsequent activities | Number |
| `is_critical` | Indicates whether the activity is critical within the project path or not | Boolean |
| `is_new_ativity` | Indicates whether the activity was recently added or not | Boolean |
| `unique_correlative_id` | Unique and correlative identifier within the activity. Value displayed in the 'UID' field | Number |
| `organization_id` | Identifier of the organization to which the project belongs to | Number |
| `baseline_start_date` | Baseline start date of the activity from the active baseline version. Null if no baseline exists | Date (nullable) |
| `baseline_end_date` | Baseline end date of the activity from the active baseline version. Null if no baseline exists | Date (nullable) |
| `baseline_duration` | Baseline duration of the activity in days from the active baseline version. Null if no baseline exists | Number (nullable) |

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
| 400 | Required URL parameters are either missing from the request or are invalid. | The `projectId` parameter was not provided in the URL or its not a valid integer. |
| 401 | Unauthorized access: required auth information is missing from the request. | Insufficient authorization data was provided |
| 401 | Unauthorized access: organization id is invalid or is not permitted. | The token does not correspond to a valid organization |
| 401 | Unauthorized access: user role is invalid or is not permitted. | `The token does not correspond to a valid role, or it does not grant sufficient access permissions |
| 401 | Unauthorized access: user id is invalid or is not permitted. | The token does not correspond to a valid user |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Example request using cURL

Use the following curl example to connect to the production endpoint (substitute {projectId} by an integer value):

```bash
  curl -X GET "https://datahub.outbuild.com/activities/project/{projectId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /activities/project/{projectId}/schedule/{scheduleId}

### Description

*This endpoint retrieves a list of an organization's activities for a specific schedule of a project.*

> **📄 Pagination**: The endpoint returns **500** activities per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/activities/project/{projectId}/schedule/{scheduleId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/activities/project/13/schedule/1?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/activities/project/13/schedule/1`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of activities for a specific organization and project. If no activities are available for the specific project or it doesn't exist, the response body will be empty (`[]`).

##### Example response

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "page":1,
    "hasNextPage": true,
    "activities": [
      {
        "id": 14971,
        "parent_id": 43,
        "unique_id": 6524,
        "description": null,
        "name": "Plumbing - Water Lines & Tubs",
        "duration": 5,
        "cost_budgeted": 0,
        "progress": 100,
        "constraint_date": "2016-01-06 08:00:00.000",
        "start_date": "2016-01-06 08:00:00.000",
        "end_date": "2016-04-20 17:00:00.000",
        "constraint_type": "As soon As Possible",
        "activiy_type" : "task",
        "correlative_id": 3066,
        "has_child_activities": false,
        "labor_hours_earned": 0,
        "weight": 4.80656,
        "created_at": "2016-03-05 19:23:33.947Z",
        "updated_at": "2023-01-06 15:10:23.890Z",
        "gantt_id": 4321,
        "schedule_id": 98,
        "calendar_id": 3,
        "cost_actual": 0,
        "cost_earned": 0,
        "labor_hours_budgeted": 0,
        "sum_of_duration_recursively": 0,
        "company_id": 23,
        "free_float": 0,
        "is_critical": false,
        "is_new_ativity": false,
        "unique_correlative_id": 144,
        "organization_id": 12,
        "baseline_start_date": "2016-01-06T08:00:00.000",
        "baseline_end_date": "2016-04-20T17:00:00.000",
        "baseline_duration": 5
      }
      ... // more objects with the same structure
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

**Click to view a detailed explanation of the fields for each activity**

| Name | Description | Type |
|---|---|---|
| `id` | Unique activity identifier | Number |
| `parent_id` | Identifier of the parent activity, if applicable | Number |
| `unique_id` | Unique identifier of the activity within the schedule | Number |
| `description` | Description of the activity | Text |
| `name` | Name of the activity | Text |
| `duration` | Duration of the activity in days | Number |
| `cost_budgeted` | Budgeted cost assigned to the activity | Number |
| `progress` | Current progress of the activity expressed as a percentage (0 to 100) | Number |
| `constraint_date` | Date of the constraint applied to the activity | Date |
| `start_date` | Planned start date of the activity | Date |
| `end_date` | Planned end date of the activity | Date |
| `constraint_type` | Type of constraint applied (e.g., ASAP, ALAP, SNET, FNET, SNLT, FNLT, MSO, or MFO) | Text |
| `activiy_type` | Type of activity. E.g., milestone, task, or project (when it is a parent activity). | Text |
| `correlative_id` | Correlative identifier of the activity. Indicates the order of the activity in a schedule. | Number |
| `has_child_activities` | Indicates whether the activity has child activities | Boolean |
| `labor_hours_earned` | Accumulated labor hours based on the progress made to date | Number |
| `weight` | Weight of the activity in relation to its parent activity | Number |
| `created_at` | Timestamp indicating when the activity was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the project was last updated | Date in UTC (Zulu Zone) |
| `gantt_id` | Identifier of the associated Gantt schedule | Number |
| `schedule_id` | Identifier of the schedule to which the activity belongs to | Number |
| `calendar_id` | Identifier of the calendar associated with the activity | Number |
| `cost_actual` | Actual cost incurred to date for the activity | Number |
| `cost_earned` | Earned cost value of the activity based on current progress | Number |
| `labor_hours_budgeted` | Budgeted labor hours to complete the activity | Number |
| `sum_of_duration_recursively` | Sum of the duration of all related activities (including child activities). | Number |
| `company_id` | Identifier of the company responsible for the activity | Number |
| `free_float` | Amount of days an activity can be delayed without affecting the start of subsequent activities | Number |
| `is_critical` | Indicates whether the activity is critical within the project path or not | Boolean |
| `is_new_ativity` | Indicates whether the activity was recently added or not | Boolean |
| `unique_correlative_id` | Unique and correlative identifier within the activity. Value displayed in the 'UID' field | Number |
| `organization_id` | Identifier of the organization to which the project belongs to | Number |
| `baseline_start_date` | Baseline start date of the activity from the active baseline version. Null if no baseline exists | Date (nullable) |
| `baseline_end_date` | Baseline end date of the activity from the active baseline version. Null if no baseline exists | Date (nullable) |
| `baseline_duration` | Baseline duration of the activity in days from the active baseline version. Null if no baseline exists | Number (nullable) |

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
| 400 | Required URL parameters are either missing from the request or are invalid. | Either the `projectId` or the `scheduleId` parameter was not provided in the URL, or it is not a valid integer. |
| 401 | Unauthorized access: required auth information is missing from the request. | Insufficient authorization data was provided |
| 401 | Unauthorized access: organization id is invalid or is not permitted. | The token does not correspond to a valid organization |
| 401 | Unauthorized access: user role is invalid or is not permitted. | The token does not grant sufficient access permissions |
| 401 | Unauthorized access: user id is invalid or is not permitted. | The token does not correspond to a valid user |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Example request using cURL

Use the following curl example to connect to the production endpoint (substitute {projectId} and {scheduleId} by an integer values):

```bash
  curl -X GET "https://datahub.outbuild.com/activities/project/{projectId}/schedule/{scheduleId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /activities/schedule/{scheduleId}/historical-progress

### Description

*This endpoint retrieves the historical activity progress for all activities in a specific schedule. For each activity and each day where progress was recorded, the last progress value of that day is returned.*

> **📄 Pagination**: The endpoint returns **500** records per request  
> **📉 Sorting**: Items are returned sorted by activity ID (ascending) and date (descending, most recent first).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/activities/schedule/{scheduleId}/historical-progress?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/activities/schedule/98/historical-progress?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/activities/schedule/98/historical-progress`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of historical progress records for all activities in the specified schedule. If no historical progress data is available for the schedule, the response body will be empty (`[]`).

##### Example response

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "page": 1,
    "hasNextPage": true,
    "historical_activity_progress": [
      {
        "id": 38221909,
        "progress": 56.74,
        "created": "2022-01-04T12:25:48.000",
        "activity_id": 495845,
        "date": "2022-01-04"
      },
      {
        "id": 37440275,
        "progress": 56.74,
        "created": "2021-12-29T09:52:12.000",
        "activity_id": 495845,
        "date": "2021-12-29"
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

**Click to view a detailed explanation of the fields for each historical activity progress record**

| Name | Description | Type |
|---|---|---|
| `id` | Unique identifier of the historical progress record | Number |
| `progress` | Progress of the activity at the time of recording, expressed as a percentage (0 to 100) | Number |
| `created` | Timestamp indicating when the progress was recorded | Date |
| `activity_id` | Identifier of the activity this progress record belongs to | Number |
| `date` | The date on which the progress was recorded (only the last record per day per activity is returned) | Date |

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
| 400 | Required URL parameters are either missing from the request or are invalid. | The `scheduleId` parameter was not provided in the URL or its not a valid integer. |
| 401 | Unauthorized access: required auth information is missing from the request. | Insufficient authorization data was provided |
| 401 | Unauthorized access: organization id is invalid or is not permitted. | The token does not correspond to a valid organization |
| 401 | Unauthorized access: user role is invalid or is not permitted. | The token does not grant sufficient access permissions |
| 401 | Unauthorized access: user id is invalid or is not permitted. | The token does not correspond to a valid user |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Example request using cURL

Use the following curl example to connect to the production endpoint (substitute {scheduleId} by an integer value):

```bash
  curl -X GET "https://datahub.outbuild.com/activities/schedule/{scheduleId}/historical-progress?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```
