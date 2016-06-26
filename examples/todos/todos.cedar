enum Status {
  Todo,
  Complete,
  Deleted
}

record Unit {}
record Todo {
  id Int
  deadline DateTime
  description String
  status Status
}

fn getTodos() [Todo]
fn getTodo(id Int) Todo?
fn addTodo(deadline DateTime, description String) Todo
fn deleteTodo(id Int) Unit
