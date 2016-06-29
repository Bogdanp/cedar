port module Main exposing (main)

import Echo exposing (ClientConfig, defaultConfig, echo)
import Html exposing (text)
import Html.App as Html
import HttpBuilder as HB
import Task


type Msg
    = EchoError (HB.Error String)
    | EchoSuccess (HB.Response String)


conf : ClientConfig
conf =
    defaultConfig "http://localhost:9090/echo"


init : ( String, Cmd Msg )
init =
    let
        message =
            "hello"
    in
        message
            ! [ echo conf message
                    |> Task.perform EchoError EchoSuccess
              ]


update : Msg -> String -> ( String, Cmd Msg )
update msg message =
    case msg of
        EchoError err ->
            message ! [ fail [ "invalid response from server: " ++ toString err ] ]

        EchoSuccess { data } ->
            if data == message then
                message ! [ succeed () ]
            else
                message
                    ! [ fail
                            [ "expected '" ++ message ++ "' but got '" ++ data ++ "'"
                            ]
                      ]


main : Program Never
main =
    Html.program
        { init = init
        , update = update
        , view = always (text "")
        , subscriptions = always Sub.none
        }


succeed : () -> Cmd msg
succeed () =
    respond { success = True, messages = [ "all tests passed" ] }


fail : List String -> Cmd msg
fail ms =
    respond { success = False, messages = ms }


type alias Result =
    { success : Bool
    , messages : List String
    }


port respond : Result -> Cmd msg
