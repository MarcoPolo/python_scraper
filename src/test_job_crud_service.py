import os
import sys
import unittest
import tempfile
import config
import uuid
import time
from datetime import datetime, timedelta
from job_crud_service import JobCRUDService
from job import Job
from db_helper import SQLiteHelper

epoch_start = datetime(1970,1,1)

test_job_object = {
    "name": "Spang",
    "email": "Jane.Doe@gmail.com",
    "phone": "4086212997",
    "arrival_date": "2020-05-10",
    "departure_date": "2020-05-12",
    "location": 0
}
class jobCRUDServiceTest(unittest.TestCase):

    def setUp(self):
        # Clear db
        self.test_db_path = os.path.dirname(__file__) + '/test.db';
        try:
            os.remove(self.test_db_path)
        except OSError:
            pass

        open(self.test_db_path, 'w').close()
        # Create new db
        self.db = SQLiteHelper(self.test_db_path)
        with open(os.path.dirname(__file__) + '/../migrations/base.sql', 'r') as base_sql_file:
            base_sql=base_sql_file.read()
            statements = base_sql.split(';')
            for statement in statements:
                self.db.execute(statement, False)
        with open(os.path.dirname(__file__) + '/../migrations/populate_sites.sql', 'r') as site_data:
            site_data_sql = site_data.read()
            statements = base_sql.split(';')
            for statement in statements:
                self.db.execute(statement, False)
        self.service = JobCRUDService(override=self.test_db_path)

    def test_correct_db_on_init(self):
        # Test that we're testing the right DB :P
        assert self.service.db_path is not None
        assert self.service.db_path is self.test_db_path
        # Test default db
        defaultCrudService = JobCRUDService()
        assert defaultCrudService.db_path is config.db_path

    def test_empty_db(self):
        jobs = self.service.get_jobs()
        assert len(jobs) is 0

    def test_write_job(self):
        test_uuid = uuid.uuid4()
        job = Job(test_job_object)
        self.service.write_job(job)
        db_jobs = self.service.get_jobs()
        db_job = db_jobs[0]
        expected_arrival_date = (datetime.strptime("2020-05-10", "%Y-%m-%d") - epoch_start).total_seconds()
        assert len(db_jobs) is 1
        assert db_job.id == job.id
        assert db_job.name == job.name
        assert db_job.email == "Jane.Doe@gmail.com"
        assert db_job.phone == "4086212997"
        assert db_job.arrival_date == expected_arrival_date
        assert db_job.length_of_stay is 2
        return job.id

    def test_get_job_by_id(self):
        job = Job(test_job_object)
        self.service.write_job(job)
        retrieved_job = self.service.get_job_by_id(str(job.id))
        assert retrieved_job is not None
        assert retrieved_job.id == job.id

    def test_update_job_last_notified(self):
        job = Job(test_job_object)
        fifteen_minutes_ago = (datetime.now() - timedelta(minutes=15) - epoch_start).total_seconds()
        job.set_last_notified(fifteen_minutes_ago)
        self.service.write_job(job)
        retrieved_job = self.service.get_job_by_id(str(job.id))
        # Ignore milliseconds
        assert retrieved_job.last_notified == fifteen_minutes_ago

        self.service.update_job_last_notified(retrieved_job)
        updated_job = self.service.get_job_by_id(str(job.id))
        print updated_job.last_notified, job.last_notified
        assert updated_job.last_notified > job.last_notified

    def test_filtering_last_notified(self):
        job = Job(test_job_object)
        twenty_minutes_ago = time.time() - (20*60)
        job.set_last_notified(twenty_minutes_ago)
        self.service.write_job(job)
        list_of_jobs = self.service.get_jobs()
        assert len(list_of_jobs) == 1
        self.service.update_job_last_notified(job)
        print self.service.get_job_by_id(job.id).last_notified;
        list_of_jobs = self.service.get_jobs()
        assert len(list_of_jobs) == 0

    def tearDown(self):
        os.remove(self.test_db_path)


if __name__ == '__main__':
    unittest.main()
