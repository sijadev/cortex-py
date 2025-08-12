# ADR-004: API Design Approach and Standards

## Status
**Accepted** - 2025-08-10

## Context & Problem Statement
The Cortex system requires a consistent API design approach to support web clients, mobile applications, and service-to-service communication. We need to establish standards for API architecture, design patterns, and implementation practices that promote consistency, maintainability, and developer experience.

## Decision Drivers
- **Consistency**: Uniform API patterns across all Cortex services
- **Developer Experience**: Intuitive, well-documented APIs
- **Performance**: Efficient data transfer and minimal overhead
- **Scalability**: Support for future service expansion
- **Maintainability**: Clear, evolvable API structures
- **Standards Compliance**: Adherence to established REST principles

## Considered Options

### Option A: Strict REST with HATEOAS
**Approach**: Full REST implementation with hypermedia controls.

**Pros:**
- Theoretically pure REST implementation
- Self-documenting APIs through hypermedia
- Strong discoverability of API capabilities

**Cons:**
- Increased complexity for simple operations
- Higher bandwidth overhead
- Limited client ecosystem support for HATEOAS

### Option B: Pragmatic REST (Selected)
**Approach**: REST principles with practical compromises for usability.

**Pros:**
- Familiar HTTP verbs and status codes
- Resource-oriented URL design
- Good balance of standards and practicality
- Excellent tooling and ecosystem support

**Cons:**
- Not "pure" REST (lacks HATEOAS)
- Potential for inconsistent implementations
- May require additional documentation

### Option C: GraphQL
**Approach**: Query language and runtime for APIs.

**Pros:**
- Client-specified data requirements
- Strong type system and introspection
- Single endpoint for all operations

**Cons:**
- Additional complexity and learning curve
- Caching challenges
- Over-fetching protection requires careful design

## Decision
We will implement **Pragmatic REST** as our primary API design approach.

### Core Design Principles

#### 1. Resource-Oriented URLs
```
# Good Examples
GET    /api/v1/projects/{id}
POST   /api/v1/projects
PUT    /api/v1/projects/{id}
DELETE /api/v1/projects/{id}

# Nested Resources
GET    /api/v1/projects/{id}/adrs
POST   /api/v1/projects/{id}/adrs
```

#### 2. HTTP Method Usage
- **GET**: Retrieve resources (safe, idempotent)
- **POST**: Create resources (non-idempotent)
- **PUT**: Create/Update entire resource (idempotent)
- **PATCH**: Partial resource updates (idempotent)
- **DELETE**: Remove resources (idempotent)

#### 3. Response Format Standards
```json
{
  "data": {
    "id": "123",
    "type": "project",
    "attributes": {
      "name": "Project Alpha",
      "status": "active",
      "created_at": "2025-08-10T10:00:00Z"
    },
    "relationships": {
      "adrs": {
        "links": {
          "related": "/api/v1/projects/123/adrs"
        }
      }
    }
  },
  "meta": {
    "version": "v1",
    "timestamp": "2025-08-10T10:00:00Z"
  }
}
```

#### 4. Error Response Standards
```json
{
  "errors": [
    {
      "id": "unique_error_id",
      "status": "400",
      "code": "VALIDATION_ERROR",
      "title": "Validation Failed",
      "detail": "The 'name' field is required",
      "source": {
        "pointer": "/data/attributes/name"
      }
    }
  ],
  "meta": {
    "timestamp": "2025-08-10T10:00:00Z",
    "request_id": "req_123456"
  }
}
```

### API Versioning Strategy

#### URL-Based Versioning (Primary)
```
https://api.cortex.com/v1/projects
https://api.cortex.com/v2/projects
```

#### Header-Based Versioning (Fallback)
```http
Accept: application/vnd.cortex.v1+json
API-Version: v1
```

### Security Standards
- **Authentication**: JWT Bearer tokens for all authenticated endpoints
- **Authorization**: Role-based access control per resource
- **HTTPS**: Required for all production endpoints
- **Rate Limiting**: Implement per-user and per-endpoint limits
- **Input Validation**: Comprehensive request validation and sanitization

### Documentation Requirements

#### OpenAPI Specification
- Complete OpenAPI 3.0 specification for all endpoints
- Generated documentation with interactive examples
- Automated specification validation in CI/CD

#### Developer Resources
```
/docs/api/                 # API documentation portal
/docs/api/getting-started  # Quick start guide
/docs/api/authentication   # Auth guide
/docs/api/reference        # Complete endpoint reference
/docs/api/examples         # Code examples in multiple languages
```

## Implementation Standards

### Request/Response Patterns

#### Pagination
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 5,
    "total_count": 100
  },
  "links": {
    "first": "/api/v1/projects?page=1",
    "prev": null,
    "next": "/api/v1/projects?page=2",
    "last": "/api/v1/projects?page=5"
  }
}
```

#### Filtering and Sorting
```
GET /api/v1/projects?filter[status]=active&sort=-created_at&fields[projects]=name,status
```

#### Status Code Usage
- **200 OK**: Successful GET, PUT, PATCH
- **201 Created**: Successful POST
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Client error (validation, malformed request)
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server error

### Performance Optimizations
- **Caching**: ETags and conditional requests
- **Compression**: gzip/brotli response compression
- **Field Selection**: Sparse fieldsets to reduce payload size
- **Batch Operations**: Support for bulk create/update operations

## Testing Standards

### API Testing Requirements
- **Unit Tests**: 90%+ coverage for all endpoint handlers
- **Integration Tests**: End-to-end API workflow testing
- **Contract Tests**: OpenAPI specification validation
- **Performance Tests**: Response time and throughput benchmarks
- **Security Tests**: Authentication, authorization, and input validation

### Test Data Management
- Consistent test fixtures across all API tests
- Database seeding and cleanup for integration tests
- Mock external service dependencies

## Monitoring and Observability

### Metrics Collection
- **Response Times**: P50, P95, P99 latencies
- **Error Rates**: 4xx and 5xx response percentages
- **Throughput**: Requests per second per endpoint
- **Authentication**: Success/failure rates

### Logging Standards
```json
{
  "timestamp": "2025-08-10T10:00:00Z",
  "level": "INFO",
  "request_id": "req_123456",
  "method": "GET",
  "path": "/api/v1/projects/123",
  "status_code": 200,
  "response_time_ms": 45,
  "user_id": "user_789",
  "user_agent": "CortexClient/1.0"
}
```

## Consequences

### Positive
- ✅ Familiar REST patterns reduce learning curve
- ✅ Excellent tooling and ecosystem support
- ✅ Predictable URL structures and HTTP semantics
- ✅ Good caching and proxy support
- ✅ Clear separation of concerns

### Negative
- ❌ Potential for over-fetching or under-fetching data
- ❌ Multiple API calls may be needed for complex operations
- ❌ Less flexible than GraphQL for varying client needs
- ❌ Versioning complexity as APIs evolve

### Mitigation Strategies
- Implement field selection to reduce over-fetching
- Provide batch endpoints for common multi-resource operations
- Use comprehensive API documentation and examples
- Establish clear versioning and deprecation policies

## Confidence Assessment
**Overall Confidence**: 88%

### Breakdown
- **Evidence Weight**: 90% (Industry-standard approach, extensive precedents)
- **Experience Factor**: 85% (Team experienced with REST APIs)
- **Risk Assessment**: 85% (Well-understood approach with known challenges)
- **Time Factor**: 92% (Established patterns, good tooling available)

**Risk Mitigation**: Comprehensive API design review process, automated testing, gradual rollout

## Related Decisions
- [[ADR-001-JWT-vs-Sessions]] - API authentication strategy
- [[Cross-Vault Linking]] - Inter-service API communication
- [[System-Workflows]] - API integration with system processes

## References
- [REST API Design Best Practices](https://restfulapi.net/rest-api-design-tutorial-with-example/)
- [JSON API Specification](https://jsonapi.org/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)

---

**Confidence Calculator**: [[Confidence Calculator]]
**Primary Repository**: [[Progressive-API-Complexity-Pattern]]