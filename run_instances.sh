#!/usr/bin/env python3

readonly endpoint="$(dirname "$(realpath "${BASH_SOURCE[0]}")")/mountpoint/run_instances"

cat > "${endpoint}" << 'END'
{
	"InstanceType": "t2.nano",
	"MaxCount": 30,
	"MinCount": 30
}
END
