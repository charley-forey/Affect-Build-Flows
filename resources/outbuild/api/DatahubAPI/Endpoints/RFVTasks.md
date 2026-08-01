<!-- Source: https://pp-docs.outbuild.com/docs/DatahubAPI/Endpoints/RFVTasks -->

# RFVTasks

The endpoints described in this section retrieve the linkage between Lookahead Tasks and reasons for variance (RFV) associated with active schedules in your organization. Each row in the response represents a single connection between one RFV and one Lookahead Task, allowing customers to join RFV data with task data in their reporting tools.

# RFV Tasks

1. [Endpoint 1: GET all rfv tasks](#request-rfv-tasks)
2. [Endpoint 2: GET all rfv tasks for a specific project](#request-rfv-tasksprojectprojectid)
3. [Endpoint 3: GET all rfv tasks for a specific project and schedule](#request-rfv-tasksprojectprojectidschedulescheduleid)

## `GET` /rfv-tasks

### Description

*This endpoint retrieves a list of the connections between an organization's RFVs and their associated Lookahead Tasks. Each row represents one link: a single RFV can appear multiple times, once per linked task. RFVs with no linked tasks are not returned.*

> **📄 Pagination**: The endpoint returns **500** rfv tasks per request  
> **📉 Sorting**: Items are returned sorted by RFV ID in descending order (highest to lowest), then by task ID in descending order.

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/rfv-tasks?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/rfv-tasks?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/rfv-tasks`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of RFV-task connections for a specific organization. If no connections are available, the response body will be empty (`[]`).

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
      "rfv_tasks": [
        {
          "rfv_id": 12,
          "task_id": 1042,
          "organization_id": 2,
          "project_id": 7,
          "schedule_id": 3
        },
        {
          "rfv_id": 12,
          "task_id": 2301,
          "organization_id": 2,
          "project_id": 7,
          "schedule_id": 3
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

**Click to view a detailed explanation of the fields for each rfv task**

| Name | Description | Type |
|---|---|---|
| `rfv_id` | Identifier of the RFV in the connection | Number |
| `task_id` | Identifier of the Lookahead Task linked to the RFV | Number |
| `organization_id` | Identifier of the organization the RFV and task belong to | Number |
| `project_id` | Identifier of the project the RFV and task belong to | Number |
| `schedule_id` | Identifier of the schedule the RFV and task belong to | Number |

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
  curl -X GET "https://datahub.outbuild.com/rfv-tasks?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /rfv-tasks/project/{projectId}

### Description

*This endpoint retrieves a list of the connections between an organization's RFVs and their associated Lookahead Tasks for a specific project.*

> **📄 Pagination**: The endpoint returns **500** rfv tasks per request  
> **📉 Sorting**: Items are returned sorted by RFV ID in descending order (highest to lowest), then by task ID in descending order.

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/rfv-tasks/project/{projectId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/rfv-tasks/project/13?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/rfv-tasks/project/13`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of RFV-task connections for a specific organization and project. If no connections are available for the specific project or it doesn't exist, the response body will be empty (`[]`).

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
      "rfv_tasks": [
        {
          "rfv_id": 12,
          "task_id": 1042,
          "organization_id": 2,
          "project_id": 7,
          "schedule_id": 3
        },
        {
          "rfv_id": 12,
          "task_id": 2301,
          "organization_id": 2,
          "project_id": 7,
          "schedule_id": 3
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

**Click to view a detailed explanation of the fields for each rfv task**

| Name | Description | Type |
|---|---|---|
| `rfv_id` | Identifier of the RFV in the connection | Number |
| `task_id` | Identifier of the Lookahead Task linked to the RFV | Number |
| `organization_id` | Identifier of the organization the RFV and task belong to | Number |
| `project_id` | Identifier of the project the RFV and task belong to | Number |
| `schedule_id` | Identifier of the schedule the RFV and task belong to | Number |

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
  curl -X GET "https://datahub.outbuild.com/rfv-tasks/project/{projectId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /rfv-tasks/project/{projectId}/schedule/{scheduleId}

### Description

*This endpoint retrieves a list of the connections between an organization's RFVs and their associated Lookahead Tasks for a specific schedule of a project.*

> **📄 Pagination**: The endpoint returns **500** rfv tasks per request  
> **📉 Sorting**: Items are returned sorted by RFV ID in descending order (highest to lowest), then by task ID in descending order.

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/rfv-tasks/project/{projectId}/schedule/{scheduleId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/rfv-tasks/project/13/schedule/1?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/rfv-tasks/project/13/schedule/1`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of RFV-task connections for a specific organization, project, and schedule. If no connections are available for the specific project and schedule or they don't exist, the response body will be empty (`[]`).

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
      "rfv_tasks": [
        {
          "rfv_id": 12,
          "task_id": 1042,
          "organization_id": 2,
          "project_id": 7,
          "schedule_id": 3
        },
        {
          "rfv_id": 12,
          "task_id": 2301,
          "organization_id": 2,
          "project_id": 7,
          "schedule_id": 3
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

**Click to view a detailed explanation of the fields for each rfv task**

| Name | Description | Type |
|---|---|---|
| `rfv_id` | Identifier of the RFV in the connection | Number |
| `task_id` | Identifier of the Lookahead Task linked to the RFV | Number |
| `organization_id` | Identifier of the organization the RFV and task belong to | Number |
| `project_id` | Identifier of the project the RFV and task belong to | Number |
| `schedule_id` | Identifier of the schedule the RFV and task belong to | Number |

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
  curl -X GET "https://datahub.outbuild.com/rfv-tasks/project/{projectId}/schedule/{scheduleId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```
