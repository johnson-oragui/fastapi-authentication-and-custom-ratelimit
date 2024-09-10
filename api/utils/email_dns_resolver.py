import dns.resolver
from fastapi import HTTPException, status

from api.db.redis_database import get_redis_sync


async def check_email_deliverability(email: str):
    """
    Checks if an email address is potentially deliverable by verifying the existence of
    MX records for its domain.

    Args:
        email (str): The email address to check.

    Returns:
        None: True if MX records were found.
    Raises:
        HTTPException: if MX not found
    """
    # Extract the domain from the email address
    domain = email.split('@')[1]
    # define a cache key
    domain_key = f'mx_{domain}'
    error_message = "Email domain does not have valid MX records, contact your domain provider."
    try:
        with get_redis_sync() as redis:
            # Check cache first
            cached_result = await redis.get(domain_key)
            # return if cache is valid
            if cached_result and cached_result == '1':
                return None
            # raise exception if cache is invalid
            elif cached_result == '0':
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=error_message)

            # perform the DNS lookup asynchronously
            resolver = dns.resolver.Resolver()
            resolver.timeout = 1  # Set a timeout for the DNS query
            answers = resolver.query(domain, 'MX')

            # Check if at least one MX record was found
            if answers:
                # Store result in cache
                await redis.set(domain_key, '1', ex=3600)
                # return
                return None
            else:
                print(f"Domain not found or no answer for DNS query:  {domain}")
                # Cache failed result
                await redis.set(domain_key, '0', ex=3600)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Email domain does not have valid MX records.")

    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        print(f"Domain not found or no answer for DNS query:  {domain}")
        # Cache failed result
        await redis.set(domain_key, '0', ex=3600)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email domain does not have valid MX records.")
    except Exception as exc:
        print(f"Error checking email deliverability: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
