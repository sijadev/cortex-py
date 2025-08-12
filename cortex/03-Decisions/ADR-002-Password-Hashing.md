# ADR-002: Password Hashing Algorithm Selection

## Status
**Accepted** - 2025-08-10

## Context & Problem Statement
The Cortex authentication system requires a secure password hashing mechanism to protect user credentials. We need to select an appropriate hashing algorithm that balances security, performance, and future-proofing against evolving attack methods.

## Decision Drivers
- **Security**: Resistance to rainbow table, brute force, and dictionary attacks
- **Performance**: Acceptable computational overhead for user authentication
- **Adaptability**: Ability to adjust security parameters as hardware evolves
- **Standards Compliance**: Adherence to current security best practices
- **Implementation Maturity**: Proven, well-tested implementations available

## Considered Options

### Option A: bcrypt (Selected)
**Approach**: Adaptive hash function based on the Blowfish cipher.

**Pros:**
- Industry standard with 20+ years of battle-testing
- Adaptive cost parameter allows security scaling
- Salt generation built-in (per-password unique salts)
- Widely supported with mature library implementations
- Proven resistance to GPU-based attacks

**Cons:**
- Limited to 72-byte password inputs (truncation risk)
- Relatively slower than newer alternatives
- Fixed salt size may limit future expansion

### Option B: Argon2
**Approach**: Memory-hard function, winner of Password Hashing Competition.

**Pros:**
- State-of-the-art algorithm designed for password hashing
- Memory-hard properties resist ASIC/GPU attacks
- Three variants optimized for different use cases
- Configurable memory, time, and parallelism parameters

**Cons:**
- Newer standard with less widespread adoption
- Higher memory requirements may impact server resources
- More complex parameter tuning required

### Option C: scrypt
**Approach**: Memory-hard key derivation function.

**Pros:**
- Memory-hard properties similar to Argon2
- Well-established in cryptocurrency applications
- Configurable work factors for security tuning

**Cons:**
- Complex parameter selection
- Higher resource requirements
- Less focused on password hashing specifically

## Decision
We will implement **bcrypt** as our primary password hashing algorithm.

### Implementation Details
- **Algorithm**: bcrypt with Blowfish-based implementation
- **Cost Factor**: Start with 12 rounds (industry recommended)
- **Salt**: 128-bit random salt per password (bcrypt default)
- **Library**: Use well-maintained language-specific bcrypt libraries
- **Upgrade Path**: Design system to support algorithm migration

### Security Configuration
```javascript
// Node.js example configuration
const bcrypt = require('bcrypt');
const SALT_ROUNDS = 12; // 2^12 iterations (~250ms on modern hardware)

// Password hashing
const hashedPassword = await bcrypt.hash(password, SALT_ROUNDS);

// Password verification
const isValid = await bcrypt.compare(password, hashedPassword);
```

### Monitoring and Maintenance
- Regular benchmarking to adjust cost factor for ~200-300ms target
- Annual security review and cost factor adjustment
- Migration planning for future algorithm upgrades

## Consequences

### Positive
- ✅ Proven security track record across millions of applications
- ✅ Built-in adaptive security with tunable cost parameters
- ✅ Excellent library support and documentation
- ✅ Automatic salt handling prevents implementation errors
- ✅ Reasonable computational overhead for typical loads

### Negative
- ❌ Password length limitation (72 bytes) may affect very long passwords
- ❌ Not the newest algorithm (potential future obsolescence)
- ❌ Higher CPU usage compared to basic hash functions
- ❌ May require cost factor tuning as hardware evolves

### Mitigation Strategies
- Implement password length validation to stay within bcrypt limits
- Design authentication system for easy algorithm migration
- Regular performance monitoring and cost factor adjustment
- Prepare migration path to Argon2 for future consideration

## Security Requirements

### Implementation Standards
- **Cost Factor**: Minimum 10 rounds, recommended 12+ rounds
- **Password Policy**: Minimum 8 characters, complexity requirements
- **Rate Limiting**: Implement login attempt throttling
- **Monitoring**: Log and alert on suspicious authentication patterns

### Compliance Considerations
- **NIST Guidelines**: Follows NIST SP 800-63B recommendations
- **OWASP**: Compliant with OWASP Authentication Cheat Sheet
- **GDPR**: Supports secure password handling requirements
- **Industry Standards**: Meets common security audit requirements

## Confidence Assessment
**Overall Confidence**: 92%

### Breakdown
- **Evidence Weight**: 95% (Extensive real-world usage and security research)
- **Experience Factor**: 85% (Team familiar with bcrypt implementations)
- **Risk Assessment**: 90% (Well-understood risks with proven mitigations)
- **Time Factor**: 98% (Standard implementation, well-documented)

**Risk Mitigation**: Use established libraries, implement comprehensive testing, plan for future upgrades

## Performance Considerations

### Benchmarking Results
Based on typical server hardware (2023):
- **Cost 10**: ~65ms per hash
- **Cost 12**: ~250ms per hash (recommended)
- **Cost 14**: ~1000ms per hash (high security environments)

### Scaling Considerations
- Authentication load balancing across multiple servers
- Async password hashing to avoid blocking request processing
- Consider offloading to dedicated authentication service for high loads

## Migration Strategy

### Current Implementation
- Immediate implementation with bcrypt cost 12
- Comprehensive testing across all authentication flows
- Documentation and team training on secure implementation

### Future Considerations
- Monitor Argon2 adoption trends in enterprise environments
- Plan for gradual migration strategy if needed
- Maintain backward compatibility during any algorithm transitions

## Related Decisions
- [[ADR-001-JWT-vs-Sessions]] - Authentication token strategy
- [[Auth-System]] - Overall authentication architecture
- [[System-Workflows]] - Authentication workflow integration

## References
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [bcrypt: A Robust Password Hashing System](https://www.usenix.org/legacy/events/usenix99/provos/provos.html)

---

**Confidence Calculator**: [[Confidence Calculator]]
**Primary Repository**: [[Auth-System]]