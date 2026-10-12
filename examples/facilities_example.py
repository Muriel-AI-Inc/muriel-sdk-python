"""Example: Working with facilities and geocoding data."""

from muriel import get_state_facilities, get_facility_geocoding

API_KEY = None  # None: read MURIEL_API_KEY from the environment
# Data calls cost 1 credit per 1,000 records returned, added up across calls.


def example_get_state_facilities():
    """Get all facilities in a state with geocoding data."""
    print("Getting facilities in Illinois...")
    print("-" * 60)

    facilities = get_state_facilities(
        state="IL",
        api_key=API_KEY,
        limit=50,
    )

    print(f"Found {facilities['facility_count']} facilities")
    print()

    # Show first 5 facilities with geocoding
    print("First 5 facilities with geocoding:")
    count = 0
    for facility in facilities["facilities"]:
        if facility.get("geocoding"):
            geo = facility["geocoding"]
            print(f"\n{count + 1}. {facility['pwsid']}")
            print(f"   System: {facility.get('system_name', 'N/A')}")
            print(f"   Facility ID: {facility['facility_state_assigned_id']}")
            print(f"   Location: {geo['latitude']}, {geo['longitude']}")
            print(f"   Address: {geo.get('address_formatted', 'N/A')}")
            print(f"   Confidence: {geo.get('confidence', 'N/A')}%")

            count += 1
            if count >= 5:
                break


def example_get_specific_facility():
    """Get geocoding for a specific facility."""
    print("\nGetting specific facility geocoding...")
    print("-" * 60)

    facility = get_facility_geocoding(
        pwsid="IL0316000",
        facility_id="FAC001",
        api_key=API_KEY,
    )

    if facility["found"]:
        geo = facility["geocoding"]
        print(f"Facility found!")
        print(f"  PWSID: {facility['pwsid']}")
        print(f"  Facility ID: {facility['facility_state_assigned_id']}")
        print(f"  Location: {geo['latitude']}, {geo['longitude']}")
        print(f"  Address: {geo.get('address_formatted', 'N/A')}")
        print(f"  Source: {geo.get('source', 'N/A')}")
    else:
        print("Facility not found or no geocoding data available")


if __name__ == "__main__":
    print("=" * 60)
    print("MURIEL SDK - FACILITIES & GEOCODING EXAMPLES")
    print("=" * 60)
    print()

    example_get_state_facilities()
    example_get_specific_facility()

    print()
    print("=" * 60)
