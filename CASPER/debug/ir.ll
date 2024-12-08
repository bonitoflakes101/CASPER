; ModuleID = "main"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

define i32 @"main"()
{
main_entry:
  %".2" = alloca i32
  store i32 10, i32* %".2"
  %".4" = alloca i32
  store i32 15, i32* %".4"
  %".6" = alloca float
  store float 0x4036333340000000, float* %".6"
  %".8" = alloca float
  store float 0x4010ccccc0000000, float* %".8"
  ret i32 69
}
