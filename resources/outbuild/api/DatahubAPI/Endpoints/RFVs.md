<!-- Source: https://pp-docs.outbuild.com/docs/DatahubAPI/Endpoints/RFVs -->

# RFVs

The endpoints described in this section retrieve information on reasons for variance (RFV) associated with active schedules in your organization.

# Rfvs

1. [Endpoint 1: GET all rfvs](#request-rfvs)
2. [Endpoint 2: GET all rfvs for a specific project](#request-rfvsprojectprojectid)
3. [Endpoint 3: GET all rfvs for a specific project and schedule](#request-rfvsprojectprojectidschedulescheduleid)

## `GET` /rfvs

### Description

*This endpoint retrieves a list of an organization's rfvs.*

> **📄 Pagination**: The endpoint returns **500** rfvs per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/rfvs?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/rfvs?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/rfvs`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of rfvs for a specific organization. If no rfvs are available, the response body will be empty (`[]`).

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
      "rfvs": [
        {
          "id": 12,
          "name": "Fire Sprinkler rework needed",
          "priority": "low",
          "week": 40,
          "status": "resolved",
          "picture": "https://gravatar.com/avatar/4affd2d24f11e09c58f34dc529847bda?s=400&d=robohash&r=x",
          "created_at": "2016-03-05 19:23:33.947Z",
          "updated_at": "2023-01-06 15:10:23.890Z",
          "type_id": 9,
          "created_by": 10,
          "schedule_id": 3,
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

**Click to view a detailed explanation of the fields for each rfv**

| Name | Description | Type |
|---|---|---|
| `id` | Unique rfv identifier | Number |
| `name` | Name associated to the reason for variance (RFV) | Text |
| `priority` | RFV's priority (low,normal, high or urgent) | Text |
| `week` | Week number (1-52) | Number |
| `picture` | URL with an image associated to the RFV | Text |
| `created_at` | Timestamp indicating when the RFV was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the RFV was last updated | Date in UTC (Zulu Zone) |
| `type_id` | Identifier of the associated RFV Type | Number |
| `created_by` | Identifier of the user that created the RFV | Number |
| `schedule_id` | Identifier of the schedule to which the RFV belongs to | Number |

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
  curl -X GET "https://datahub.outbuild.com/rfvs?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /rfvs/project/{projectId}

### Description

*This endpoint retrieves a list of an organization's users for a specific project.*

> **📄 Pagination**: The endpoint returns **500** users per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/users/project/{projectId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/users/project/13?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/users/project/13`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of users for a specific organization and project. If no users are available for the specific project or it doesn't exist, the response body will be empty (`[]`).

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
      "rfvs": [
        {
          "id": 12,
          "name": "Fire Sprinkler rework needed",
          "priority": "low",
          "week": 40,
          "status": "resolved",
          "picture": "https://gravatar.com/avatar/4affd2d24f11e09c58f34dc529847bda?s=400&d=robohash&r=x",
          "created_at": "2016-03-05 19:23:33.947Z",
          "updated_at": "2023-01-06 15:10:23.890Z",
          "type_id": 9,
          "created_by": 10,
          "schedule_id": 3,
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

**Click to view a detailed explanation of the fields for each rfv**

| Name | Description | Type |
|---|---|---|
| `id` | Unique rfv identifier | Number |
| `name` | Name associated to the reason for variance (RFV) | Text |
| `priority` | RFV's priority (low,normal, high or urgent) | Text |
| `week` | Week number (1-52) | Number |
| `picture` | URL with an image associated to the RFV | Text |
| `created_at` | Timestamp indicating when the RFV was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the RFV was last updated | Date in UTC (Zulu Zone) |
| `type_id` | Identifier of the associated RFV Type | Number |
| `created_by` | Identifier of the user that created the RFV | Number |
| `schedule_id` | Identifier of the schedule to which the RFV belongs to | Number |

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
  curl -X GET "https://datahub.outbuild.com/rfvs/project/{projectId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /rfvs/project/{projectId}/schedule/{scheduleId}

### Description

*This endpoint retrieves a list of an organization's rfvs for a specific schedule of a project.*

> **📄 Pagination**: The endpoint returns **500** rfvs per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/rfvs/project/{projectId}/schedule/{scheduleId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/rfvs/project/13/schedule/1?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/rfvs/project/13/schedule/1`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of rfvs for a specific organization and project. If no rfvs are available for the specific project or it doesn't exist, the response body will be empty (`[]`).

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
      "rfvs": [
        {
          "id": 12,
          "name": "Fire Sprinkler rework needed",
          "priority": "low",
          "week": 40,
          "status": "resolved",
          "picture": "https://gravatar.com/avatar/4affd2d24f11e09c58f34dc529847bda?s=400&d=robohash&r=x",
          "created_at": "2016-03-05 19:23:33.947Z",
          "updated_at": "2023-01-06 15:10:23.890Z",
          "type_id": 9,
          "created_by": 10,
          "schedule_id": 3,
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

**Click to view a detailed explanation of the fields for each rfv**

| Name | Description | Type |
|---|---|---|
| `id` | Unique rfv identifier | Number |
| `name` | Name associated to the reason for variance (RFV) | Text |
| `priority` | RFV's priority (low,normal, high or urgent) | Text |
| `week` | Week number (1-52) | Number |
| `picture` | URL with an image associated to the RFV | Text |
| `created_at` | Timestamp indicating when the RFV was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the RFV was last updated | Date in UTC (Zulu Zone) |
| `type_id` | Identifier of the associated RFV Type | Number |
| `created_by` | Identifier of the user that created the RFV | Number |
| `schedule_id` | Identifier of the schedule to which the RFV belongs to | Number |

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
  curl -X GET "https://datahub.outbuild.com/rfvs/project/{projectId}/schedule/{scheduleId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```
