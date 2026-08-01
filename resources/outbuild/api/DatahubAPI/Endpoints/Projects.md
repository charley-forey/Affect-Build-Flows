<!-- Source: https://pp-docs.outbuild.com/docs/DatahubAPI/Endpoints/Projects -->

# Projects

The endpoints described in this section retrieve information on active projects and schedules in your organization.

1. [Endpoint 1: GET all projects](#request-projects)
2. [Endpoint 2: GET project by id](#request-projectsprojectid)

## `GET` /projects

### Description

*This endpoint retrieves a list of an organization's projects, each projects with its associated schedules.*

> **📄 Pagination**: The endpoint returns **100** projects per page  
> **📉 Sorting**: Items are returned sorted by IDs in descending order (highest to lowest), including sublists.

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/projects?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/projects?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/projects`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of projects for a specific organization. Each project includes a list of schedules, if any exist. If no schedules are available for any project, the schedules field will be empty (`[]`).

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
    "projects": [
      {
        "id": 123,
        "name": "Project Alpha",
        "planification_day": "0",
        "timezone": "UTC",
        "country": "US",
        "currency": "USD",
        "budget": 500000,
        "size_type": "Large",
        "size": 10000,
        "image": "url_to_image",
        "type": "Construction",
        "stage": "Planning",
        "archive_reason": null,
        "pcr_goal": 85,
        "pcc_goal": 90,
        "task_creter": "duration",
        "activity_creter": "duration",
        "created_at": "2023-12-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "address": "123 Main St",
        "manager_id": 10,
        "procore_id": "123456",
        "schedules" : [
          {
            "id": 101,
            "name": "Schedule 1",
            "description": "Main construction schedule",
            "status": "Active",
            "order": 1,
            "productive": true,
            "created_at": "2023-12-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "hours_per_day": 8,
            "hours_per_week": 40,
            "date_format": "mm/dd/yyyy",
            "did_close_week": false,
            "current_closed_week": true,
            "is_current_schedule": true,
            "is_visible": true
          },
          ... // more objects with the same structure if any exist
        ]
      },
      ... // more objects with the same structure if any exists
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

**Click to view a detailed explanation of the fields for each project**

| Name | Description | Type |
|---|---|---|
| `id` | Unique project identifier | Number |
| `name` | Project name | Text |
| `planification_day` | Indicates the project's planning day, marking the start of a new planning week. Values range from 0 (Monday) to 6 (Sunday) | Number |
| `timezone` | Project time zone | Text |
| `country` | Project country | Text |
| `currency` | Project currency | Text |
| `budget` | Allocated project budget | Number |
| `size_type` | Project size unit | Text |
| `size` | Project size | Number |
| `image` | URL of the image associated with the project | Text |
| `type` | Project type name | Text |
| `stage` | Phase of the project (e.g., started, ended, etc.) | Text |
| `archive_reason` | Shows the reason for archiving the project; the value is null if the project was never archived | Text |
| `pcr_goal` | PCR goal (Percentage of Completion Rate) defined in the project configurations | Number |
| `pcc_goal` | PCC goal (Percentage of Commitment Compliance) defined in the project configurations | Number |
| `task_creter` | Criterion used to calculate the weighted score of tasks | Text |
| `activity_creter` | Criterion used to calculate the weighted score of activities | Text |
| `created_at` | Timestamp indicating when the project was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the project was last updated | Date in UTC (Zulu Zone) |
| `address` | Project address | Text |
| `manager_id` | Identifier of the project manager assigned to the project | Number |
| `procore_id` | Identifier of the Procore project associated with the Outbuild project (only applicable if there is an active integration with Procore) | Number |
| `schedules` | List of specific schedules ssociated with the projects | Array of Objects |

**Click to view a detailed explanation of the fields for each schedule**

| Name | Description | Type |
|---|---|---|
| `id` | Unique schedule identifier | Number |
| `name` | Schedule name | Text |
| `description` | Schedule description | Text |
| `status` | Status of the schedule | Text |
| `order` | Order of the schedule within the project. | Number |
| `productive` | Indicates whether the program is productive or not | Boolean |
| `created_at` | Timestamp indicating when the schedule was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the schedule was last updated | Date in UTC (Zulu Zone) |
| `hours_per_day` | Number of hours per day configured in the project | Number |
| `hours_per_week` | Number of hours per week configured in the project | Number |
| `date_format` | Date format used in the schedule | Text |
| `did_close_week` | Indicates whether the manual closure of the current planning week has been executed | Boolean |
| `current_closed_week` | Indicates whether the current planning week is closed in the schedule or not | Boolean |
| `is_current_schedule` | Indicates whether the schedule is defined as a 'Master Schedule' or not | Boolean |
| `is_visible` | Indicates whether the schedule is visible or not | Boolean |

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
| 401 | Unauthorized access: user role is invalid or is not permitted. | `The token does not correspond to a valid role, or it does not grant sufficient access permissions |
| 401 | Unauthorized access: user id is invalid or is not permitted. | The token does not correspond to a valid user |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Example request using cURL

Use the following curl example to connect to the production endpoint:

```bash
  curl -X GET "https://datahub.outbuild.com/projects?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /projects/{projectId}

### Description

*This endpoint retrieves a specific project an organization's, each projects with its associated schedules.*

> **📄 Pagination**: N/A, endpoint returns at most one item.  
> **📉 Sorting**: N/A, endpoint returns at most one item.

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| Prod:`https://datahub.outbuild.com/projects/{projectId}`Dev:`https://datahub-dev.outbuild.com/projects/{projectId}` | `authorizationToken` | N/A |
| Prod: | `https://datahub.outbuild.com/projects/{projectId}` |  |
| Dev: | `https://datahub-dev.outbuild.com/projects/{projectId}` |  |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

An integer value for `projectId` must be provided in the URL, e.g., `https://datahub.outbuild.com/projects/11`.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing details of a specific project, identified by its projectId, provided as a URL parameter. The retreived project includes a list of schedules, if any exist. If no schedules are available, the list will be empty (`[]`).

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
    "project":
      {
        "id": 123,
        "name": "Project Alpha",
        "planification_day": "0",
        "timezone": "UTC",
        "country": "US",
        "currency": "USD",
        "budget": 500000,
        "size_type": "Large",
        "size": 10000,
        "image": "url_to_image",
        "type": "Construction",
        "stage": "Planning",
        "archive_reason": null,
        "pcr_goal": 85,
        "pcc_goal": 90,
        "task_creter": "duration",
        "activity_creter": "duration",
        "created_at": "2023-12-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "address": "123 Main St",
        "manager_id": 10,
        "procore_id": "123456",
         "schedules" : [
          {
            "id": 101,
            "name": "Schedule 1",
            "description": "Main construction schedule",
            "status": "Active",
            "order": 1,
            "productive": true,
            "created_at": "2023-12-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "hours_per_day": 8,
            "hours_per_week": 40,
            "date_format": "mm/dd/yyyy",
            "did_close_week": false,
            "current_closed_week": true,
            "is_current_schedule": true,
            "is_visible": true
          },
          ... // more objects with the same structure if any exist
        ]
      }
  }
}
```

#### Properties overview

You can find information about each data field in the sections below.

**Click to view a detailed explanation of the fields of the retrieved project**

| Name | Description | Type |
|---|---|---|
| `id` | Unique project identifier | Number |
| `name` | Project name | Text |
| `planification_day` | Indicates the project's planning day, marking the start of a new planning week. Values range from 0 (Monday) to 6 (Sunday) | Number |
| `timezone` | Project time zone | Text |
| `country` | Project country | Text |
| `currency` | Project currency | Text |
| `budget` | Allocated project budget | Number |
| `size_type` | Project size unit | Text |
| `size` | Project size | Number |
| `image` | URL of the image associated with the project | Text |
| `type` | Project type name | Text |
| `stage` | Phase of the project (e.g., started, ended, etc.) | Text |
| `archive_reason` | Shows the reason for archiving the project; the value is null if the project was never archived | Text |
| `pcr_goal` | PCR goal (Percentage of Completion Rate) defined in the project configurations | Number |
| `pcc_goal` | PCC goal (Percentage of Commitment Compliance) defined in the project configurations | Number |
| `task_creter` | Criterion used to calculate the weighted score of tasks | Text |
| `activity_creter` | Criterion used to calculate the weighted score of activities | Text |
| `created_at` | Timestamp indicating when the project was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the project was last updated | Date in UTC (Zulu Zone) |
| `address` | Project address | Text |
| `manager_id` | Identifier of the project manager assigned to the project | Number |
| `procore_id` | Identifier of the Procore project associated with the Outbuild project (only applicable if there is an active integration with Procore) | Number |
| `schedules` | List of specific schedules ssociated with the projects | Array of Objects |

**Click to view a detailed explanation of the fields for each schedule**

| Name | Description | Type |
|---|---|---|
| `id` | Unique schedule identifier | Number |
| `name` | Schedule name | Text |
| `description` | Schedule description | Text |
| `status` | Status of the schedule | Text |
| `order` | Order of the schedule within the project. | Number |
| `productive` | Indicates whether the program is productive or not | Boolean |
| `created_at` | Timestamp indicating when the schedule was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the schedule was last updated | Date in UTC (Zulu Zone) |
| `hours_per_day` | Number of hours per day configured in the project | Number |
| `hours_per_week` | Number of hours per week configured in the project | Number |
| `date_format` | Date format used in the schedule | Text |
| `did_close_week` | Indicates whether the manual closure of the current planning week has been executed | Boolean |
| `current_closed_week` | Indicates whether the current planning week is closed in the schedule or not | Boolean |
| `is_current_schedule` | Indicates whether the schedule is defined as a 'Master Schedule' or not | Boolean |
| `is_visible` | Indicates whether the schedule is visible or not | Boolean |

#### ⚠️Failure

The endpoint will return the following response if the request fails:

```json
  {
    "statusCode" : ERROR_CODE,
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
| 404 | No data matching the query was found. | Project with the given `projectId` does not exist |
| 400 | Required URL parameters are either missing from the request or are invalid. | The `projectId` parameter was not provided in the URL or its not a valid integer. |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Production request example using cURL

Use the following curl example to connect to the production endpoint:

```bash
  curl -X GET "https://datahub.outbuild.com/projects/{projectId}" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```
