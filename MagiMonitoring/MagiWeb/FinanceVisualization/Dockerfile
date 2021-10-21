FROM mcr.microsoft.com/dotnet/sdk:3.1 AS build
WORKDIR /build

SHELL ["/bin/bash", "--login", "-c"]
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash
RUN nvm install 14.4.0

COPY ./*.csproj .
RUN dotnet restore

COPY . .
WORKDIR /build
RUN dotnet publish -c release -o published --no-cache

FROM mcr.microsoft.com/dotnet/aspnet:3.1
WORKDIR /app
COPY --from=build /build/published ./
ENTRYPOINT ["dotnet", "FinanceVisualization.dll"]
