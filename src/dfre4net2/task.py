from typing import Optional
from datetime import datetime
from enum import Enum

class Priority(Enum):
        CRITICAL=1
        HIGH=2
        MID=3
        LOW=4
class Task():
    #Priority enum is inside the class otherwise pickle does not work

    #Everything could None for a Task becauce it can be used as a dummy task for planning purpose
    def __init__(self,data:Optional[object]=None,process:Optional[object]=None,definition_of_done:Optional[object]=None, task_id:Optional[str]=None, requester_agent_id:Optional[list]=None, 
                 executer_agent_id:Optional[list]=None, priority:Optional[Priority]=None,start_time:Optional[datetime]=None,end_time:Optional[datetime]=None,description:Optional[str]=None) -> None:
        self.data = data
        self.process = process
        self.definition_of_done = definition_of_done
        self.task_id=task_id
        self.executer_agent_id=executer_agent_id
        self.requester_agent_id=requester_agent_id
        self.priority=priority
        self.start_time=start_time
        self.end_time=end_time
        self.description=description
        self.isTaskComplete=False
        msg=""
        if(description is not None):
            msg=f"A new task created for {description}"
        if(task_id is not None):
            msg=msg+f" with task id: {task_id}"
        if(requester_agent_id is not None):
            msg=msg+f" for agent id: {requester_agent_id}"
        print(msg)
        
    def execute(self):
        self.start_time=datetime.now()
        if(self.definition_of_done==None):
            result=self.process(self.data)
        else:
            result=self.process(self.data,self.definition_of_done)
        self.end_time=datetime.now()
        return result