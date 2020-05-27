# ec2fs 

ec2fs is an amazon ec2 interface written as fuse filesystem

## /proc fs similarity 

It's similar to /proc fs in case of its design - it's mainly read-only (you cannot create, modifiy, or delete file directly).

## filesystem structure

/instances/\<instance\_id> - RO - attributes of an EC2 instance
/run\_instances - WO - endpoint for creating instances

### TODO
- create /terminate\_instances WO endpoint
- create /stats RO endpoint (with stats about requests made to Amazon)
- initizalize fs with existing instances
- better logging
