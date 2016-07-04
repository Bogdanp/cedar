enum Status {
  Todo,
  Complete,
  Deleted
}

record Unit {}
record Todo {
  id Int
  deadline Timestamp
  description String
  status Status
}

fn getTodos() [Todo]
fn getTodo(id Int) Todo?
fn addTodo(deadline Timestamp, description String) Todo
fn deleteTodo(id Int) Unit
