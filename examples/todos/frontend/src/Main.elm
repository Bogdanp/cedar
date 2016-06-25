module Main exposing (main)

import Api.Todos as Todos exposing (Todo)
import Date
import Html exposing (..)
import Html.App as Html exposing (program)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick, onInput)
import HttpBuilder as HB
import Task


config : Todos.ClientConfig
config =
    Todos.defaultConfig "/todos"


type Msg
    = GetTodosError (HB.Error String)
    | GetTodosSuccess (HB.Response (List Todo))
    | AddTodoError (HB.Error String)
    | AddTodoSuccess (HB.Response Todo)
    | AddTodo
    | DeleteTodoError (HB.Error String)
    | DeleteTodoSuccess Int (HB.Response Todos.Unit)
    | DeleteTodo Int
    | ChangeDescription String


type alias Model =
    { error : Maybe String
    , todos : List Todo
    , description : String
    }


init : ( Model, Cmd Msg )
init =
    { error = Nothing
    , todos = []
    , description = ""
    }
        ! [ Todos.getTodos config
                |> Task.perform GetTodosError GetTodosSuccess
          ]


update : Msg -> Model -> ( Model, Cmd Msg )
update msg ({ todos } as model) =
    case msg of
        GetTodosError e ->
            { model | error = Just <| toString e } ! []

        GetTodosSuccess { data } ->
            { model | todos = data } ! []

        AddTodoError e ->
            { model | error = Just <| toString e } ! []

        AddTodoSuccess { data } ->
            { model | todos = data :: todos } ! []

        AddTodo ->
            { model | description = "" }
                ! [ Todos.addTodo config (Date.fromTime 1466886892044) model.description
                        |> Task.perform AddTodoError AddTodoSuccess
                  ]

        DeleteTodoError e ->
            { model | error = Just <| toString e } ! []

        DeleteTodoSuccess id { data } ->
            { model | todos = List.filter (.id >> (/=) id) todos } ! []

        DeleteTodo id ->
            model
                ! [ Todos.deleteTodo config id
                        |> Task.perform DeleteTodoError (DeleteTodoSuccess id)
                  ]

        ChangeDescription description ->
            { model | description = description } ! []


view : Model -> Html Msg
view { error, todos, description } =
    div []
        [ h1 [] [ text "Todos" ]
        , p [] [ text <| Maybe.withDefault "" error ]
        , ul [] (List.map todo todos)
        , input
            [ onInput ChangeDescription
            , type' "text"
            , value description
            ]
            []
        , input
            [ onClick AddTodo
            , type' "button"
            , value "Add"
            ]
            []
        ]


todo : Todo -> Html Msg
todo { id, description } =
    li []
        [ text description
        , input
            [ onClick (DeleteTodo id)
            , type' "button"
            , value "x"
            ]
            []
        ]


main : Program Never
main =
    program
        { init = init
        , update = update
        , view = view
        , subscriptions = always Sub.none
        }
