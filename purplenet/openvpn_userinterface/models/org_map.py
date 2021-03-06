# encoding: utf-8
# vim: shiftwidth=4 expandtab

from django.db import models
from django.contrib.auth.models import Group

from .siteconfig import InterestingEnvVar

class MappingType(models.Model):
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=400)
    source_name = models.CharField(max_length=200)
    
    NAMESPACE_CHOICES = [
        ("env", "Environment variables")
    ]
    namespace = models.CharField(max_length=30, choices=NAMESPACE_CHOICES,
        default="env")

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = "openvpn_userinterface"

class OrgMapping(models.Model):
    group = models.ForeignKey(Group)
    # REVERSE: element_set = ForeignKey(MappingElement)

    def __unicode__(self):
        return u"%s %s" % (
            self.group.name,
    
            u", ".join(u'%s:%s="%s"' % (
                elem.type.namespace,
                elem.type.source_name,
                elem.value
            ) for elem in self.element_set.all())
        )

    class Meta:
        app_label = "openvpn_userinterface"

class MappingElement(models.Model):
    type = models.ForeignKey(MappingType, related_name="element_set")
    mapping = models.ForeignKey(OrgMapping, related_name="element_set")
    value = models.CharField(max_length=200)

    def matches(self, client):
        if self.type.namespace != "env":
            raise AssertionError("The only implemented namespace is 'env'")
        
        value_from_env = os.environ.get(self.type.source_name, None)
        return self.value == value_from_env

    def __unicode__(self):
        return u"%s=%s" % (self.type.source_name, self.value)

    class Meta:
        app_label = "openvpn_userinterface"

def load_org_map(org_map, restrict_groups=None):
    # XXX restrict_groups unimplemented

    for line in org_map.split(";"):
        line = line.strip()
        if not line:
            continue
        
        target_name, the_rest = line.split("<-", 1);
        target = Group.objects.get(name=target_name.strip())
        
        mapping = OrgMapping(group=target)
        mapping.save()
        
        elements = the_rest.split("&")
        for element_str in elements:
            source_name, value = element_str.split("=", 1)
            source_name, value = source_name.strip(), value.strip()
            namespace = "env"
            
            # Make sure this environment variable is queried in
            # update_group_membership.
            InterestingEnvVar.objects.get_or_create(name=source_name)

            mapping_type, created = MappingType.objects.get_or_create(
                namespace=namespace,
                source_name=source_name, 
                
                defaults=dict(
                    name="%s (%s)" % (source_name, namespace),
                    description="Auto-generated by load_org_map"
                )
            )
            
            element = MappingElement(
                type=mapping_type,
                mapping=mapping,
                value=value
            )
            element.save()

def dump_org_map(mappings=None):
    if mappings is None:
        mappings = OrgMapping.objects.order_by("group__name")

    # TODO Inflate this code, it's way too dense
    return "\n".join(
        "%s <- %s;" % (
            mapping.group.name,
            " & ".join("%s=%s" % (element.type.source_name, element.value)
                for element in mapping.element_set.all())
        ) for mapping in mappings
    )
    
def validate_org_map(org_map):
    # XXX Stub
    return
