# ADR-001: JWT vs Sessions for Authentication

## Status
**Accepted** - 2025-08-10

## Context & Problem Statement
The Cortex system requires a robust authentication mechanism that can support both web-based interfaces and API access. We need to decide between traditional server-side sessions and stateless JWT (JSON Web Tokens) for managing user authentication and authorization.

## Decision Drivers
- **Scalability**: Support for horizontal scaling and microservices architecture
- **Performance**: Minimal overhead for authentication checks
- **Security**: Secure token handling and session management
- **Flexibility**: Support for multiple client types (web, mobile, API)
- **Complexity**: Implementation and maintenance overhead

## Considered Options

### Option A: Traditional Server-Side Sessions
**Approach**: Store session data on the server with session IDs in client cookies.

**Pros:**
- Well-established pattern with extensive library support
- Server-side session control (easy invalidation)
- Smaller client-side storage footprint
- Built-in CSRF protection mechanisms

**Cons:**
- Requires shared session storage for scaling (Redis/database)
- Stateful server design complicates horizontal scaling
- Limited support for mobile/API clients
- Session store becomes a single point of failure

### Option B: JWT Tokens (Selected)
**Approach**: Stateless authentication using cryptographically signed JSON Web Tokens.

**Pros:**
- Stateless design supports horizontal scaling
- Self-contained tokens reduce database lookups
- Excellent API and mobile client support
- Supports distributed microservices architecture
- Industry-standard with broad ecosystem support

**Cons:**
- Larger token size increases bandwidth overhead
- Token revocation complexity (requires blacklisting)
- Sensitive data exposure risk if tokens compromised
- More complex refresh token implementation

## Decision
We will implement **JWT-based authentication** as our primary authentication mechanism.

### Implementation Details
- **Access Tokens**: Short-lived (15 minutes) JWT tokens for API access
- **Refresh Tokens**: Long-lived (7 days) tokens stored securely for token renewal
- **Token Storage**: HTTP-only cookies for web clients, secure storage for mobile
- **Security**: RS256 signing algorithm with rotating keys
- **Payload**: Minimal claims (user ID, roles, expiration) to reduce token size

### Security Measures
- Refresh token rotation on each use
- Token blacklisting for critical revocation scenarios
- Short access token lifetimes to limit exposure window
- Secure token storage mechanisms per client type

## Consequences

### Positive
- ✅ Enables stateless, horizontally scalable architecture
- ✅ Simplified authentication for API clients and services  
- ✅ Reduced database load for authentication checks
- ✅ Standards-based approach with good tooling support
- ✅ Future-proof for microservices migration

### Negative
- ❌ More complex token lifecycle management
- ❌ Requires robust key management infrastructure
- ❌ Token revocation requires additional mechanisms
- ❌ Larger network overhead compared to session IDs
- ❌ Security risks if tokens are not properly secured

### Mitigation Strategies
- Implement comprehensive token monitoring and alerting
- Use short-lived access tokens to minimize exposure
- Build robust refresh token rotation mechanisms
- Establish key rotation procedures and monitoring
- Create token revocation service for critical scenarios

## Confidence Assessment
**Overall Confidence**: 85%

### Breakdown
- **Evidence Weight**: 90% (Industry best practices, proven at scale)
- **Experience Factor**: 75% (Team has moderate JWT experience)
- **Risk Assessment**: 80% (Well-understood risks with known mitigations)
- **Time Factor**: 95% (Adequate time for proper implementation)

**Risk Mitigation**: Phased rollout starting with API endpoints, comprehensive security testing

## Related Decisions
- [[ADR-002-Password-Hashing]] - Password security implementation
- [[ADR-003-Projekt-Kapselung]] - Related to authentication boundaries
- [[Auth-System]] - Overall authentication architecture

## References
- [RFC 7519: JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Auth0: JWT vs Sessions](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)

---

**Confidence Calculator**: [[Confidence Calculator]]
**Primary Repository**: [[Auth-System]]