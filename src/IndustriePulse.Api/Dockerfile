FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY ["src/IndustriePulse.Api/IndustriePulse.Api.csproj", "src/IndustriePulse.Api/"]
COPY ["src/IndustriePulse.MachineState/IndustriePulse.MachineState.csproj", "src/IndustriePulse.MachineState/"]

RUN dotnet restore "src/IndustriePulse.Api/IndustriePulse.Api.csproj"

COPY . .

RUN dotnet publish "src/IndustriePulse.Api/IndustriePulse.Api.csproj" \
    -c Release \
    -o /app/publish \
    --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app

ENV ASPNETCORE_HTTP_PORTS=8080
EXPOSE 8080

COPY --from=build /app/publish .

USER $APP_UID

ENTRYPOINT ["dotnet", "IndustriePulse.Api.dll"]
