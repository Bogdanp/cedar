module Main exposing (main)

import Api.Todos as Todos exposing (Todo)
import Date exposing (Date)
import DatePicker exposing (DatePicker)
import Html exposing (..)
import Html.App as Html exposing (program)
import Html.Attributes exposing (href, rel, type', value)
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
    | ToDatePicker DatePicker.Msg
    | ChangeDescription String


type alias Model =
    { error : Maybe String
    , todos : List Todo
    , date : Date
    , datepicker : DatePicker
    , description : String
    }


init : ( Model, Cmd Msg )
init =
    let
        ( datepicker, datepickerFx ) =
            DatePicker.init DatePicker.defaultSettings
    in
        { error = Nothing
        , todos = []
        , date = Date.fromTime 1466886892044
        , datepicker = datepicker
        , description = ""
        }
            ! [ Todos.getTodos config
                    |> Task.perform GetTodosError GetTodosSuccess
              , Cmd.map ToDatePicker datepickerFx
              ]


update : Msg -> Model -> ( Model, Cmd Msg )
update msg ({ todos, date } as model) =
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
                ! [ Todos.addTodo config date model.description
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

        ToDatePicker msg ->
            let
                ( datepicker, datepickerFx, mdate ) =
                    DatePicker.update msg model.datepicker
            in
                { model
                    | date = Maybe.withDefault date mdate
                    , datepicker = datepicker
                }
                    ! [ Cmd.map ToDatePicker datepickerFx ]

        ChangeDescription description ->
            { model | description = description } ! []


view : Model -> Html Msg
view { error, todos, datepicker, description } =
    div []
        [ node "link"
            [ rel "stylesheet"
            , href "http://bogdanp.github.io/elm-datepicker/elm-datepicker.css"
            ]
            []
        , h1 [] [ text "Todos" ]
        , p [] [ text <| Maybe.withDefault "" error ]
        , ul [] (List.map todo todos)
        , input
            [ onInput ChangeDescription
            , type' "text"
            , value description
            ]
            []
        , DatePicker.view datepicker
            |> Html.map ToDatePicker
        , input
            [ onClick AddTodo
            , type' "button"
            , value "Add"
            ]
            []
        ]


todo : Todo -> Html Msg
todo { id, deadline, description } =
    li []
        [ text description
        , text " ("
        , text <| showDate deadline
        , text ")"
        , input
            [ onClick (DeleteTodo id)
            , type' "button"
            , value "x"
            ]
            []
        ]


showDate : Date -> String
showDate d =
    toString (Date.month d) ++ " " ++ toString (Date.day d) ++ ", " ++ toString (Date.year d)


main : Program Never
main =
    program
        { init = init
        , update = update
        , view = view
        , subscriptions = always Sub.none
        }
