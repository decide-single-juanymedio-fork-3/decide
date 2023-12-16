from django.db import models
from django.contrib.auth.models import User


class Census(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)

class CensusGroup(models.Model):
    groupName = models.TextField(unique=True)
    voters = models.ManyToManyField(User, related_name='voted_groups')
    voting_id = models.PositiveIntegerField(null=True, blank=True)

    def applyCensus(self):
        if self.voting_id is not None and self.voting_id != '':
            for v in self.voters.all():
                existing_census = Census.objects.filter(voter_id=v.id, voting_id=self.voting_id).first()
                if existing_census is None:
                    Census.objects.create(voting_id=self.voting_id, voter_id=v.id)

    def __str__(self):
        return "Group - " + self.groupName



