<!-- Source: https://pp-docs.outbuild.com/docs/DatahubAPI/Endpoints/Weekly%20Commitments -->

# Weekly Commitments

The endpoints described in this section retrieve information on weekly commitments associated with active schedules in your organization.

# Weekly commitments

1. [Endpoint 1: GET all weekly commitments](#request-commitments)
2. [Endpoint 2: GET all weekly commitments for a specific project](#request-commitmentsprojectprojectid)
3. [Endpoint 3: GET all weekly commitments for a specific project and schedule](#request-commitmentsprojectprojectidschedulescheduleid)

## `GET` /commitments

### Description

*This endpoint retrieves a list of an organization's commitments.*

> **📄 Pagination**: The endpoint returns **100** commitments per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/commitments?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/commitments?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/commitments`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of commitments for a specific organization. If no commitments are available, the response body will be empty (`[]`).

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
      "commitments": [
        {
          "id": 123,
          "commitment_tasks": 2,
          "week": 12,
          "start_date": "2016-01-06 08:00:00.000",
          "end_date": "2016-04-20 17:00:00.000",
          "realized_tasks": 1,
          "created_at": "2016-03-05 19:23:33.947Z",
          "updated_at": "2023-01-06 15:10:23.890Z",
          "schedule_id": 12,
          "closed": true,
          "year": 2024,
          "company_id": 54,
          "taskcommitments": [
            {
              "id": 3,
              "weekly_commitment":,
              "progress_at_close_week":,
              "created_at": "2016-03-05 19:23:33.947Z",
              "updated_at": "2023-01-06 15:10:23.890Z",
              "task_id": 677,
              "responsible_user_id":,
              "progress_at_start_week":,
              "start_date": "2016-01-06 08:00:00.000",
              "end_date": "2016-01-8 17:00:00.000",
              "duration": 2,
              "crew_size": 0,
              "task_name": "Schedule mechanical final inspection",
              "company_name": "Outbuild",
              "company_id": 3
            },
            ... // more objects with the same structure
          ]
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

**Click to view a detailed explanation of the fields for each commitment**

| Name | Description | Type |
|---|---|---|
| `id` | Unique commitment identifier | Number |
| `commitment_tasks` | Total number of tasks committed for the week | Number |
| `week` | Week number (1-52) | Number |
| `start_date` | Start date of the weekly commitment | Date |
| `end_date` | End date of the weekly commitment. | Date |
| `realized_tasks` | Number of tasks completed by the end of the week | Number |
| `created_at` | Timestamp indicating when the week commitment was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the week commitment was last updated | Date in UTC (Zulu Zone) |
| `schedule_id` | Identifier of the schedule to which the weekly commitment belong to | Number |
| `closed` | Indicates whether the weekly commitment was closed or not | Boolean |
| `year` | Year of the weekly commitment | Number |
| `company_id` | Identifier of the company responsible for the weekly commitment | Number |
| `taskcommitments` | List of specific task commitments associated with the weekly commitment | Array of objects |

**Click to view a detailed explanation of the fields for each task commitment**

| Name | Description | Type |
|---|---|---|
| `id` | Unique task commitment identifier | Number |
| `weekly_commitment` | Committed progress of the task for the week (0-100) | Number |
| `progress_at_close_week` | Progress percentage at the end of the week for the task commitment (0-100). | Number |
| `created_at` | Timestamp indicating when the task commitment was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the task commitment was last updated | Date in UTC (Zulu Zone) |
| `task_id` | Identifier of the lookeahed task associated with the commitment | Number |
| `responsible_user_id` | Identifier of the user responsible for the task commitment | Number |
| `progress_at_start_week` | Progress percentage of the task at the start of the week (0-100). | Number |
| `start_date` | Planned start date for the task (at the time the task was committed) | Date |
| `end_date` | Planned end date for the task (at the time the task was committed) | Date |
| `duration` | Duration of the task in days (at the time the task was committed) | Number |
| `crew_size` | Size of the crew needed to perform the task (at the time the task was committed) | Number |
| `task_name` | Name of the committed task | Text |
| `company_name` | Name of the company responsible for the task. | Text |
| `company_id` | Identifier of the company responsible for the task. | Number |

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
  curl -X GET "https://datahub.outbuild.com/commitments?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /commitments/project/{projectId}

### Description

*This endpoint retrieves a list of an organization's commitments for a specific schedule of a project.*

> **📄 Pagination**: The endpoint returns **100** commitments per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/commitments/project/{projectId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/commitments/project/13?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/commitments/project/13`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of commitments for a specific organization and project. If no commitments are available for the specific project or it doesn't exist, the response body will be empty (`[]`).

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
      "commitments": [
        {
          "id": 123,
          "commitment_tasks": 2,
          "week": 12,
          "start_date": "2016-01-06 08:00:00.000",
          "end_date": "2016-04-20 17:00:00.000",
          "realized_tasks": 1,
          "created_at": "2016-03-05 19:23:33.947Z",
          "updated_at": "2023-01-06 15:10:23.890Z",
          "schedule_id": 12,
          "closed": true,
          "year": 2024,
          "company_id": 54,
          "taskcommitments": [
            {
              "id": 3,
              "weekly_commitment":,
              "progress_at_close_week":,
              "created_at": "2016-03-05 19:23:33.947Z",
              "updated_at": "2023-01-06 15:10:23.890Z",
              "task_id": 677,
              "responsible_user_id":,
              "progress_at_start_week":,
              "start_date": "2016-01-06 08:00:00.000",
              "end_date": "2016-01-8 17:00:00.000",
              "duration": 2,
              "crew_size": 0,
              "task_name": "Schedule mechanical final inspection",
              "company_name": "Outbuild",
              "company_id": 3
            },
            ... // more objects with the same structure
          ]
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

**Click to view a detailed explanation of the fields for each commitment**

| Name | Description | Type |
|---|---|---|
| `id` | Unique commitment identifier | Number |
| `commitment_tasks` | Total number of tasks committed for the week | Number |
| `week` | Week number (1-52) | Number |
| `start_date` | Start date of the weekly commitment | Date |
| `end_date` | End date of the weekly commitment. | Date |
| `realized_tasks` | Number of tasks completed by the end of the week | Number |
| `created_at` | Timestamp indicating when the week commitment was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the week commitment was last updated | Date in UTC (Zulu Zone) |
| `schedule_id` | Identifier of the schedule to which the weekly commitment belong to | Number |
| `closed` | Indicates whether the weekly commitment was closed or not | Boolean |
| `year` | Year of the weekly commitment | Number |
| `company_id` | Identifier of the company responsible for the weekly commitment | Number |
| `taskcommitments` | List of specific task commitments associated with the weekly commitment | Array of objects |

**Click to view a detailed explanation of the fields for each task commitment**

| Name | Description | Type |
|---|---|---|
| `id` | Unique task commitment identifier | Number |
| `weekly_commitment` | Committed progress of the task for the week (0-100) | Number |
| `progress_at_close_week` | Progress percentage at the end of the week for the task commitment (0-100). | Number |
| `created_at` | Timestamp indicating when the task commitment was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the task commitment was last updated | Date in UTC (Zulu Zone) |
| `task_id` | Identifier of the lookeahed task associated with the commitment | Number |
| `responsible_user_id` | Identifier of the user responsible for the task commitment | Number |
| `progress_at_start_week` | Progress percentage of the task at the start of the week (0-100). | Number |
| `start_date` | Planned start date for the task (at the time the task was committed) | Date |
| `end_date` | Planned end date for the task (at the time the task was committed) | Date |
| `duration` | Duration of the task in days (at the time the task was committed) | Number |
| `crew_size` | Size of the crew needed to perform the task (at the time the task was committed) | Number |
| `task_name` | Name of the committed task | Text |
| `company_name` | Name of the company responsible for the task. | Text |
| `company_id` | Identifier of the company responsible for the task. | Number |

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
| 401 | Unauthorized access: user role is invalid or is not permitted. | The token does not grant sufficient access permissions |
| 401 | Unauthorized access: user id is invalid or is not permitted. | The token does not correspond to a valid user |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Example request using cURL

Use the following curl example to connect to the production endpoint:

```bash
  curl -X GET "https://datahub.outbuild.com/commitments/project/{projectId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /commitments/project/{projectId}/schedule/{scheduleId}

### Description

*This endpoint retrieves a list of an organization's commitments for a specific schedule of a project.*

> **📄 Pagination**: The endpoint returns **100** commitments per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/commitments/project/{projectId}/schedule/{scheduleId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/commitments/project/13/schedule/1?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/commitments/project/13/schedule/1`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of commitments for a specific organization and project. If no commitments are available for the specific project or it doesn't exist, the response body will be empty (`[]`).

##### Example response

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
      "commitments": [
        {
          "id": 123,
          "commitment_tasks": 2,
          "week": 12,
          "start_date": "2016-01-06 08:00:00.000",
          "end_date": "2016-04-20 17:00:00.000",
          "realized_tasks": 1,
          "created_at": "2016-03-05 19:23:33.947Z",
          "updated_at": "2023-01-06 15:10:23.890Z",
          "schedule_id": 12,
          "closed": true,
          "year": 2024,
          "company_id": 54,
          "taskcommitments": [
            {
              "id": 3,
              "weekly_commitment":,
              "progress_at_close_week":,
              "created_at": "2016-03-05 19:23:33.947Z",
              "updated_at": "2023-01-06 15:10:23.890Z",
              "task_id": 677,
              "responsible_user_id":,
              "progress_at_start_week":,
              "start_date": "2016-01-06 08:00:00.000",
              "end_date": "2016-01-8 17:00:00.000",
              "duration": 2,
              "crew_size": 0,
              "task_name": "Schedule mechanical final inspection",
              "company_name": "Outbuild",
              "company_id": 3
            },
            ... // more objects with the same structure
          ]
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

**Click to view a detailed explanation of the fields for each commitment**

| Name | Description | Type |
|---|---|---|
| `id` | Unique commitment identifier | Number |
| `commitment_tasks` | Total number of tasks committed for the week | Number |
| `week` | Week number (1-52) | Number |
| `start_date` | Start date of the weekly commitment | Date |
| `end_date` | End date of the weekly commitment. | Date |
| `realized_tasks` | Number of tasks completed by the end of the week | Number |
| `created_at` | Timestamp indicating when the week commitment was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the week commitment was last updated | Date in UTC (Zulu Zone) |
| `schedule_id` | Identifier of the schedule to which the weekly commitment belong to | Number |
| `closed` | Indicates whether the weekly commitment was closed or not | Boolean |
| `year` | Year of the weekly commitment | Number |
| `company_id` | Identifier of the company responsible for the weekly commitment | Number |
| `taskcommitments` | List of specific task commitments associated with the weekly commitment | Array of objects |

**Click to view a detailed explanation of the fields for each task commitment**

| Name | Description | Type |
|---|---|---|
| `id` | Unique task commitment identifier | Number |
| `weekly_commitment` | Committed progress of the task for the week (0-100) | Number |
| `progress_at_close_week` | Progress percentage at the end of the week for the task commitment (0-100). | Number |
| `created_at` | Timestamp indicating when the task commitment was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the task commitment was last updated | Date in UTC (Zulu Zone) |
| `task_id` | Identifier of the lookeahed task associated with the commitment | Number |
| `responsible_user_id` | Identifier of the user responsible for the task commitment | Number |
| `progress_at_start_week` | Progress percentage of the task at the start of the week (0-100). | Number |
| `start_date` | Planned start date for the task (at the time the task was committed) | Date |
| `end_date` | Planned end date for the task (at the time the task was committed) | Date |
| `duration` | Duration of the task in days (at the time the task was committed) | Number |
| `crew_size` | Size of the crew needed to perform the task (at the time the task was committed) | Number |
| `task_name` | Name of the committed task | Text |
| `company_name` | Name of the company responsible for the task. | Text |
| `company_id` | Identifier of the company responsible for the task. | Number |

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

Use the following curl example to connect to the production endpoint:

```bash
  curl -X GET "https://datahub.outbuild.com/commitments/project/{projectId}/schedule/{scheduleId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```
