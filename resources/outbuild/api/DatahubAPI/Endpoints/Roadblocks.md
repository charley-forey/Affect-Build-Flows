<!-- Source: https://pp-docs.outbuild.com/docs/DatahubAPI/Endpoints/Roadblocks -->

# Roadblocks

The endpoints described in this section retrieve information on roadblocks associated with active schedules in your organization.

# Roadblocks

1. [Endpoint 1: GET all roadblocks](#request-roadblocks)
2. [Endpoint 2: GET all roadblocks for a specific project](#request-roadblocksprojectprojectid)
3. [Endpoint 3: GET all roadblocks for a specific project and schedule](#request-roadblocksprojectprojectidschedulescheduleid)

## `GET` /roadblocks

### Description

*This endpoint retrieves a list of an organization's roadblocks.*

> **📄 Pagination**: The endpoint returns **500** roadblocks per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/roadblocks?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/roadblocks?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/roadblocks`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of roadblocks for a specific organization. If no roadblocks are available, the response body will be empty (`[]`).

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
    "roadblocks": [
      {
        "id": 123,
        "name": "Specify Gas Shutdown Requirement",
        "priority": "Low",
        "type_id": 94,
        "responsible_user_id": 213,
        "required_date": "2021-11-02 15:28:08.000",
        "created_at": "2016-03-05 19:23:33.947Z",
        "updated_at": "2023-01-06 15:10:23.890Z",
        "schedule_id": 9,
        "release_date": "2021-11-03 17:28:00.000",
        "release_by": 12,
        "report_to": 50,
        "created_by": 5,
        "description": "Not a requirement on Drawing E.2.3 or the Electrical Specifications",
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

**Click to view a detailed explanation of the fields for each roadblock**

| Name | Description | Type |
|---|---|---|
| `id` | Unique roadblock identifier | Number |
| `name` | Roadblock name | Text |
| `priority` | Roadblock priority (low, normal, high, or urgent) | Text |
| `type_id` | Identifier of the associated roablock type | Number |
| `responsible_user_id` | Identifier of the user responsible for the roadblock | Number |
| `required_date` | Timestamp indicating when the roadblock is required to be released | Date |
| `created_at` | Timestamp indicating when the user was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the user was last updated | Date in UTC (Zulu Zone) |
| `schedule_id` | Identifier of the associated schedule | Number |
| `release_date` | Timestamp indicating when the roadblock was released | Date |
| `release_by` | Identifier of the user that released the roadblock | Number |
| `report_to` | Identifier of the user to report to | Number |
| `created_by` | Identifier of the user that created the roadblock | Number |
| `description` | Roadblock description | Text |

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
  curl -X GET "https://datahub.outbuild.com/roadblocks?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /roadblocks/project/{projectId}

### Description

*This endpoint retrieves a list of an organization's roadblocks for a specific project.*

> **📄 Pagination**: The endpoint returns **500** roadblocks per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/roadblocks/project/{projectId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/roadblocks/project/13?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/roadblocks/project/13`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of roadblocks for a specific organization and project. If no roadblocks are available for the specific project or it doesn't exist, the response body will be empty (`[]`).

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
    "roadblocks": [
      {
        "id": 123,
        "name": "Specify Gas Shutdown Requirement",
        "priority": "Low",
        "type_id": 94,
        "responsible_user_id": 213,
        "required_date": "2021-11-02 15:28:08.000",
        "created_at": "2016-03-05 19:23:33.947Z",
        "updated_at": "2023-01-06 15:10:23.890Z",
        "schedule_id": 9,
        "release_date": "2021-11-03 17:28:00.000",
        "release_by": 12,
        "report_to": 50,
        "created_by": 5,
        "description": "Not a requirement on Drawing E.2.3 or the Electrical Specifications",
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

**Click to view a detailed explanation of the fields for each roadblock**

| Name | Description | Type |
|---|---|---|
| `id` | Unique roadblock identifier | Number |
| `name` | Roadblock name | Text |
| `priority` | Roadblock priority (low, normal, high, or urgent) | Text |
| `type_id` | Identifier of the associated roablock type | Number |
| `responsible_user_id` | Identifier of the user responsible for the roadblock | Number |
| `required_date` | Timestamp indicating when the roadblock is required to be released | Date |
| `created_at` | Timestamp indicating when the user was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the user was last updated | Date in UTC (Zulu Zone) |
| `schedule_id` | Identifier of the associated schedule | Number |
| `release_date` | Timestamp indicating when the roadblock was released | Date |
| `release_by` | Identifier of the user that released the roadblock | Number |
| `report_to` | Identifier of the user to report to | Number |
| `created_by` | Identifier of the user that created the roadblock | Number |
| `description` | Roadblock description | Text |

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
  curl -X GET "https://datahub.outbuild.com/roadblocks/project/{projectId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /roadblocks/project/{projectId}/schedule/{scheduleId}

### Description

*This endpoint retrieves a list of an organization's roadblocks for a specific schedule of a project.*

> **📄 Pagination**: The endpoint returns **500** roadblocks per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/roadblocks/project/{projectId}/schedule/{scheduleId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/roadblocks/project/13/schedule/1?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/roadblocks/project/13/schedule/1`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of roadblocks for a specific organization and project. If no roadblocks are available for the specific project or it doesn't exist, the response body will be empty (`[]`).

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
    "roadblocks": [
      {
        "id": 123,
        "name": "Specify Gas Shutdown Requirement",
        "priority": "Low",
        "type_id": 94,
        "responsible_user_id": 213,
        "required_date": "2021-11-02 15:28:08.000",
        "created_at": "2016-03-05 19:23:33.947Z",
        "updated_at": "2023-01-06 15:10:23.890Z",
        "schedule_id": 9,
        "release_date": "2021-11-03 17:28:00.000",
        "release_by": 12,
        "report_to": 50,
        "created_by": 5,
        "description": "Not a requirement on Drawing E.2.3 or the Electrical Specifications",
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

**Click to view a detailed explanation of the fields for each roadblock**

| Name | Description | Type |
|---|---|---|
| `id` | Unique roadblock identifier | Number |
| `name` | Roadblock name | Text |
| `priority` | Roadblock priority (low, normal, high, or urgent) | Text |
| `type_id` | Identifier of the associated roablock type | Number |
| `responsible_user_id` | Identifier of the user responsible for the roadblock | Number |
| `required_date` | Timestamp indicating when the roadblock is required to be released | Date |
| `created_at` | Timestamp indicating when the user was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the user was last updated | Date in UTC (Zulu Zone) |
| `schedule_id` | Identifier of the associated schedule | Number |
| `release_date` | Timestamp indicating when the roadblock was released | Date |
| `release_by` | Identifier of the user that released the roadblock | Number |
| `report_to` | Identifier of the user to report to | Number |
| `created_by` | Identifier of the user that created the roadblock | Number |
| `description` | Roadblock description | Text |

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
  curl -X GET "https://datahub.outbuild.com/roadblocks/project/{projectId}/schedule/{scheduleId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```
